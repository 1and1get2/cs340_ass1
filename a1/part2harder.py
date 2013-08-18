import sys, os, signal, time, threading

def request_resource(proc, name, pid):
    print(name, 'priority:', pid, '- just about to request resource')
    controller_write.write('{0}:request\n'.format(pid))
    response = proc.read.readline()
    print(name, 'priority:', pid, '- got resource')
    
def release_resource(name, pid):
    controller_write.write('{0}:release\n'.format(pid))
    print(name, 'priority:', pid, '- released resource')
    
# These functions are to be scheduled and run in separate real processes.

def low_func(proc):
    pid = os.getpid() # who am I?
    request_resource(proc, 'Low', pid)
    
    sum = 0
    for i in range(100000000):
        sum += i

    request_resource(proc, 'Low', pid)
    request_resource(proc, 'Low', pid)

    release_resource('Low', pid)
    release_resource('Low', pid)
    release_resource('Low', pid)
    print('Low priority:', pid, '- finished')

def mid_func(proc):
    for i in range(1, 11):
        print('Mid priority:', i)
        time.sleep(0.5)

def high_func(proc):
    pid = os.getpid() # who am I?
    request_resource(proc, 'High', pid)
    
    sum = 0
    for i in range(100000000):
        sum += i

    release_resource('High', pid)
    
    request_resource(proc, 'High', pid)
    
    sum = 0
    for i in range(100000000):
        sum += i

    release_resource('High', pid)


    
#===============================================================================
# All of your code goes here.   
#===============================================================================



controller = Controller()
scheduler = Scheduler()
processes = {}

low_process = SimpleProcess(1, low_func)
scheduler.add_process(low_process)

threading.Thread(target=scheduler.run).start()

time.sleep(0.5) # give low_process a chance to get going

mid_process = SimpleProcess(5, mid_func)
scheduler.add_process(mid_process)

high_process_1 = SimpleProcess(10, high_func)
high_process_2 = SimpleProcess(10, high_func)

scheduler.add_process(high_process_1)
scheduler.add_process(high_process_2)

controller.run()

print('finished')

