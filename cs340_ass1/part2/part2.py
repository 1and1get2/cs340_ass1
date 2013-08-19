
import sys, os, signal, time, threading



# These functions are to be scheduled and run in separate real processes.
def low_func(proc):
    pid = os.getpid()  # who am I?
    print('Low priority:', pid, '- just about to request resource')
    controller_write.write('{0}:request\n'.format(pid))
    response = proc.read.readline()
    print('Low priority:', pid, '- got resource')
                           
    sum = 0
    for i in range(100000000):
        sum += i

    controller_write.write('{0}:release\n'.format(pid))
    print('Low priority:', pid, '- released resource')
        
    for i in range(100000000):
        sum += i

    print('Low priority:', pid, '- finished')


def mid_func(proc):
    for i in range(1, 11):
        print('Mid priority:', i)
        time.sleep(0.5)

def high_func(proc):
    pid = os.getpid()  # who am I?
    print('High priority:', pid, '- just about to request resource')
    controller_write.write('{0}:request\n'.format(pid))
    response = proc.read.readline()
    print('High priority:', pid, '- got resource')
    controller_write.write('{0}:release\n'.format(pid))
    print('High priority:', pid, '- released resource')


#===============================================================================
DEBUG = False
# DEBUG = True
class SimpleProcess():
    def __init__(self, priority, function):
        self.pid = None
        self.priority = priority
        self.func = function
        self.origin_priority = False
        self.lock = threading.RLock()
        # Set up the pipe which will later be used to send replies to the process
        # from the controller.
        r, w = os.pipe()
        self.read = os.fdopen(r)
        self.write = os.fdopen(w, mode='w', buffering=1)
    def high_priority_temp( self, current_process, bool):
        with self.lock:
            if DEBUG:
                print("mark: 77358")
                print(("increase" if bool else "decrease") + " priority ")
#             if self.
            if bool:
                if current_process.priority == scheduler.ready_list[0].priority:
                    return
                if not self.origin_priority:
                    return
                self.origin_priority = current_process.priority
                current_process.priority = scheduler.ready_list[0].priority
            else:
                current_process.priority = self.origin_priority
                self.origin_priority = False
            # resort
            if DEBUG:
                print("before resort in high_priority_temp: ")
                Scheduler.print_list(self,scheduler.ready_list)
                # starting sorting:
            scheduler.ready_list.remove(current_process)
            scheduler.ready_list.insert(len(scheduler.ready_list), current_process)
            for element in scheduler.ready_list:
                if element.priority < current_process.priority:
                    scheduler.ready_list.remove(current_process)
                    scheduler.ready_list.insert(scheduler.ready_list.index(element), current_process)
                    break
            if DEBUG:
                print("after resort in high_priority_temp: ")
                Scheduler.print_list(self, scheduler.ready_list)
            if DEBUG:
                print("check if the list still sorted after priority change: " + str(scheduler.check_list_sorted(scheduler.ready_list)))
                print("items that currently in ready_list: ")
                if scheduler.ready_list is not None: 
                    for i in scheduler.ready_list:print(" pid: " + str(i.pid) + " priority: " + str(i.priority) + " is_temp_privilage: " + str(i.origin_priority))
                else: print("")
            

    # Creates the new process for this to run in when 'run' is first called.
    def run(self):
        self.pid = os.fork()  # the child is the process
        
        if self.pid:  # in the parent
            self.read.close()
            processes[self.pid] = self
            
        else:  # in the child
            self.write.close()
            self.func(self)
            os._exit(0)  # what would happen if this wasn't here?

#===============================================================================
# This is in control of the single resource.
# Only one process at a time is allowed access to the resource.
r, w = os.pipe()
controller_read = os.fdopen(r)
controller_write = os.fdopen(w, mode='w', buffering=1)

class Controller():

    def run(self):
        owner = None
        queue = []
        lock = threading.RLock()

        while True:
            
            input_string = controller_read.readline()
            if input_string.strip() == 'terminate':
                return
            pid, message = input_string.strip().split(':')
            pid = int(pid)
            # possible race condition on line below
            with lock:
                result = "" 
                requesting_process = processes[pid]
                if message == 'request':
                    result += "\nreceived an request request from pid: " + str(pid)
                    if not owner:  # no current owner
                        result += "\nresource has no current owner, signed to pid: " + str(pid)
                        owner = requesting_process
                        owner.write.write('reply\n')
                    else:  # currently owned
                        if DEBUG:
                            print("owner.pid == pid? " + str(owner.pid) + " == " + str( pid))
                        if owner.pid == pid:
                            #already owned this resource
                            queue.append(requesting_process)
                            owner.write.write('reply\n')
                        else:
                          # owned by the others
                            owner.high_priority_temp(processes[pid],True)
                            scheduler.remove_process(requesting_process)
                            queue.append(requesting_process)

                elif message == 'release' and owner == requesting_process:
                    # the first in the queue gets it
                    result += "\nreceived an release request, pid: " + str(pid)
#                     if queue.count(owner) == 1:
#                         result += "\n decrease the priority back"
#                         owner.high_priority_temp(processes[pid],False)
                    #TODO
                    if DEBUG: print("the owner priority after release is: " + str(owner.priority))
                    if len(queue) < 1:
                        result += "\n no one in queue, clear owner"
                        owner = None
                    else:
                        if queue.count(owner) == 0:
                            # no more request from this process
                            result += "\n queue not empty, pop(0), move to ready_list "
                            owner = queue.pop(0)
                            scheduler.add_process(owner)
                            owner.high_priority_temp(processes[pid],False)
                            owner.write.write('reply\n')
                        else:
                            # still another release needed
                            owner = queue.pop(0)
                            owner.write.write('reply\n')
                else:
                    print("should not happen")
                if DEBUG:
                    print("now printing queue(pid): ")
                    for element in queue:
                        result += str(element.pid) + " "
                    print(result)
                print('owner pid:', owner.pid if owner else None)

#===============================================================================
# The dummy scheduler.
# Every second it selects the next process to run.
class Scheduler():
    def __init__(self):
        self.ready_list = []
        self.resource_lock = threading.RLock()
        origin_priority = False
        
#     def high_priority_temp( self, current_process, bool):
#         if bool:
#             origin_priority = current_process.priority
#             current_process.priority = scheduler.ready_list[0].priority
#         else:
#             current_process.priority = origin_priority
#             origin_priority = False

# 
#     # Add a process to the run list
    def add_process(self, process):
        # pass # replace with your code
        if DEBUG: 
            print("adding process: " + str(process.priority))
            for e in scheduler.ready_list:print(str(e.priority))
        self.resource_lock.acquire()
        if self.ready_list:
            # print("not empty list")
            for i in self.ready_list:
                # print("in for loop")
                if process.priority > i.priority:
                    # print("preper to insert")
                    self.ready_list.insert(self.ready_list.index(i), process)
                    self.resource_lock.release()
                    # print("readylist: " + self.ready_list)
#                     break
                    return
                else:
#                     print(" process.priority <= i.priority, skip")
                    continue
            self.ready_list.insert(len(self.ready_list), process)
                
        else:
            # print("empty list")
            self.ready_list.append(process)
        self.resource_lock.release()

    def remove_process(self, process):
        self.resource_lock.acquire()
        self.ready_list.remove(process)
        self.resource_lock.release()
#         pass # replace with your code
    # Selects the process with the best priority.
    # If more than one have the same priority these are selected in round-robin fashion.

    def check_list_sorted(self, list):
        for i in range(0, len(list) - 2):
            if list[i].priority < list[i+1].priority:
                return False
        return True
    def print_list(self, list):
        print("items that currently in the list: ")
        if list is not None: 
            for i in list:
                print(" pid: " + str(i.pid) + " priority: " + str(i.priority) + " is_temp_privilage: " + str(i.origin_priority))
        else: print(" the list is Empty")
    def select_process(self, cp, process_pos_holder):
        """sorted_list = sorted([[1,1.0345],[3,4.89],[2,5.098],[2,5.97]], key=lambda x: x[1])"""
        if DEBUG: 
            print("selecting process: ")
            print(" sorted: " + str(self.check_list_sorted(scheduler.ready_list)))
            print(" items that currently in ready_list: ")
            if scheduler.ready_list is not None: 
                for i in scheduler.ready_list:print(" pid: " + str(i.pid) + " priority: " + str(i.priority) + " is_temp_privilage: " + str(i.origin_priority))
            else: print("")

        #TODO:
        with self.resource_lock:
            result = "result start:  ======================"
            if self.ready_list:
                result += "\n list not empty"
                if cp in scheduler.ready_list:
                    result += "\n cp in scheduler.ready_list"
                    process_pos_holder = scheduler.ready_list.index(cp) + 1
                else:
                    result += "\n cp is not in scheduler.ready_list"
                    if process_pos_holder:
                        result += "\n process_pos_holder is not None, process_pos_holder remains what it was"
                        
                    else:
                        result += "\n process_pos_holder is None"
                        if DEBUG: print(result)
                        return scheduler.ready_list[0]
                for i in range(len(scheduler.ready_list)):
                    result += "\n comparing priority: " + " "
                    if scheduler.ready_list[(process_pos_holder + i) % len(scheduler.ready_list)].priority == scheduler.ready_list[0].priority:
                        result += "\n found next pocess: " + str(scheduler.ready_list[(process_pos_holder + i) % len(scheduler.ready_list)])
                        if DEBUG: print(result + "========  result end")
                        return scheduler.ready_list[(process_pos_holder + i) % len(scheduler.ready_list)]
                #TODO: ERROR
                result += "\n error happened, cant find any same priority process, details:"
                if scheduler.ready_list is not None: 
                    for i in scheduler.ready_list:result += ("\n pid: " + str(i.pid) + " priority: " + str(i.priority) + " is_temp_privilage: " + str(i.origin_priority))
                else: result += ("\nlist empty")
                if DEBUG: print(result + "\n======================  result end")
                return scheduler.ready_list[0]
            else:
                result += "\n list empty, return None\n======================  result end"
                if DEBUG: print(result)
                return None

    # Suspends the currently running process by sending it a STOP signal.
    @staticmethod
    def suspend(process):
        os.kill(process.pid, signal.SIGSTOP)

    # Resumes a process by sending it a CONT signal.
    @staticmethod
    def resume(process):
        if process.pid:  # if the process has a pid it has started
            os.kill(process.pid, signal.SIGCONT)
        else:
            process.run()
    
    def run(self):
        #TODO: added a lock here
        current_process = None
        process_pos_holder = False
        while True:
            #TODO: do we need a lock here or not
            if True:
            #with self.resource_lock:
                next_process = self.select_process(current_process, process_pos_holder if process_pos_holder else None)
                if DEBUG: print("next_process: pid: "  + str(next_process.pid) + " priority: "+ (str(next_process.priority)) if next_process else "None next process") 
#                 if next_process: print("next_process: " + str(next_process.priority)) 
#                 else: print("next_process: None")
                if next_process == None:  # no more processes
                    controller_write.write('terminate\n')
                    sys.exit()
                if next_process != current_process:
                    if current_process:
                        self.suspend(current_process)
                    current_process = next_process
                    self.resume(current_process)
                time.sleep(1)
                # need to remove dead processes from the list
                try:
                    current_process_finished = (
                        os.waitpid(current_process.pid, os.WNOHANG) != (0, 0)
                    )
                except ChildProcessError:
                    current_process_finished = True
                if current_process_finished:
                    print('remove process', current_process.pid, 'from ready list')
                    process_pos_holder = scheduler.ready_list.index(current_process)
                    self.remove_process(current_process)
                    current_process = None
        
#===============================================================================

controller = Controller()
scheduler = Scheduler()
processes = {}

# Priorities range from 1 to 10
low_process = SimpleProcess(1, low_func)
scheduler.add_process(low_process)

threading.Thread(target=scheduler.run).start()

time.sleep(0.5)  # give low_process a chance to get going

mid_process = SimpleProcess(5, mid_func)
scheduler.add_process(mid_process)
mid_process1 = SimpleProcess(5, mid_func)
scheduler.add_process(mid_process1)

high_process = SimpleProcess(10, high_func)
scheduler.add_process(high_process)
 
# high_process = SimpleProcess(5, high_func)
# scheduler.add_process(high_process)
# high_process = SimpleProcess(2, high_func)
# scheduler.add_process(high_process)
# high_process = SimpleProcess(2, high_func)
# scheduler.add_process(high_process)
# high_process = SimpleProcess(7, high_func)
# scheduler.add_process(high_process)
# high_process = SimpleProcess(9, high_func)
# scheduler.add_process(high_process)

controller.run()
if DEBUG: 
    for e in scheduler.ready_list:
        print(str(e.priority))

print('finished')

