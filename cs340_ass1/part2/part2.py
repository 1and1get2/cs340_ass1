
import sys, os, signal, time, threading
from multiprocessing.dummy import current_process


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
class SimpleProcess():
    def __init__(self, priority, function):
        self.pid = None
        self.priority = priority
        self.func = function
        # Set up the pipe which will later be used to send replies to the process
        # from the controller.
        r, w = os.pipe()
        self.read = os.fdopen(r)
        self.write = os.fdopen(w, mode='w', buffering=1)

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
                requesting_process = processes[pid]
                if message == 'request':
                    if not owner:  # no current owner
                        owner = requesting_process
                        owner.write.write('reply\n')
                    else:  # currently owned
                        scheduler.remove_process(requesting_process)
                        queue.append(requesting_process)
                elif message == 'release' and owner == requesting_process:
                    # the first in the queue gets it
                    if len(queue) < 1:
                        owner = None
                    else:
                        owner = queue.pop(0)
                        scheduler.add_process(owner)
                        owner.write.write('reply\n')
                print('owner pid:', owner.pid if owner else None)

#===============================================================================
# The dummy scheduler.
# Every second it selects the next process to run.
class Scheduler():
    def __init__(self):
        self.ready_list = []
        self.resource_lock = threading.RLock()
        origin_priority = False
    def high_priority_temp( self, current_process, high_process):
        if high_process:
            origin_priority = current_process.priority
            current_process.priority = high_process.priority
        else:
            current_process.priority = origin_priority
            origin_priority = False

# 
#     # Add a process to the run list
    def add_process(self, process):
        # pass # replace with your code
#         print("adding process: " + str(process.priority))
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

#         print("length: " + str(len(self.ready_list)))

#         print("ready_list length: " + str(len(self.ready_list)))
#         
        self.resource_lock.release()

    def remove_process(self, process):
        self.resource_lock.acquire()
        self.ready_list.remove(process)
        self.resource_lock.release()
#         pass # replace with your code
    # Selects the process with the best priority.
    # If more than one have the same priority these are selected in round-robin fashion.
    # TODO:
    def select_process(self, cp):
        if self.ready_list:
#             print("ready_list is not None")
            return self.ready_list[0]
        else:
#             print("None")
            return None
    def select_process1(self, cp):
        if self.ready_list:
            self.resource_lock.acquire()
            
#             print("in select processes: ")
#             for i in processes: print("processes [{0}]".format(i))
#             for j in scheduler.ready_list: print("ready_list: pid: " + str(j) + " priority: " + str(j.priority))
    #         scheduler.ready_list.index()
#             if cp: print("cp.priority: " + str(cp.priority) + "  cp: " + str(cp) + " index: " + str(scheduler.ready_list.index(cp)))
            if (cp is None):
                # current_process == None
#                 print("cp is None ")
                self.resource_lock.release()
                return scheduler.ready_list[0]
            else:
    #             print("current_process prioirty: " + str(current_process.priority))
#                 print("cp is not None ")
                self.resource_lock.release()
                return scheduler.ready_list[0]
        else:
            return None

    def select_process3(self, current_process_position):
        # pass # replace with your code
#         print("select process")
#         for i in scheduler.ready_list: print(i.priority)
       
        self.resource_lock.acquire()
        
        if scheduler.ready_list:
#             current_process_position = self.ready_list.index(current_process)
            for counter in range(1, len(scheduler.ready_list)):
#                 print("len(self.ready_list): " + str((current_process_position + counter) % len(self.ready_list)) + "  counter: " + str(counter))
                if self.ready_list[(current_process_position + counter) % len(self.ready_list)].priority == self.ready_list[0].priority:
                    self.resource_lock.release()
#                     print("current_process: " + str(current_process.priority))
                return self.ready_list[(current_process_position + counter) % len(self.ready_list)]
             
#              for counter in range(len(self.ready_list)):
                  
            self.resource_lock.release() 
            return self.ready_list[0]
        else:
#             print("None")
            self.resource_lock.release()
            return None
#         pass

    def select_process4(self, current_process):
        self.resource_lock.acquire()
        if len(self.ready_list) >= 1:
            if self.pos == 0:
                self.pos = self.pos + 1
                self.resource_lock.release()
                return self.ready_list[0]
            else:
                if self.pos < len(self.ready_list) - 1:
                    if self.ready_list[self.pos-1].priority == self.ready_list[self.pos].priority:
                        self.pos = self.pos + 1
                        self.lock.release()
                        return self.ready_list[self.pos]
                    else:
                        self.pos = 1
                        self.resource_lock.release()
                        return self.ready_list[0]
                else:
                    self.resource_lock.release()
        
                    return self.ready_list[0]

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
        while True:
            # print('length of ready_list:', len(self.ready_list))
#             next_process = self.select_process(self.ready_list.index(current_process) if not current_process else -1)
#             if current_process != None and current_process in self.ready_list:
#                 next_process = current_process
#             elif current_process != None:
# #                 print("current_process in the list: " + str(current_process.priority))
# #                 for process in scheduler.ready_list: print(process.priority)
#                 next_process = self.select_process(self.ready_list.index(current_process))
#             else:
# #                 print("current_process not in the list")
#                 next_process = self.select_process(-1)
# #             if next_process: print("next_process: " + str(next_process.priority)) 
# #             else: print("next_process: None")

            #TODO: do we need a lock here or not
            #if True:
            with self.resource_lock:
                next_process = self.select_process(current_process)
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

high_process = SimpleProcess(10, high_func)
scheduler.add_process(high_process)
 


controller.run()

print('finished')

