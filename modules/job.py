#!/usr/bin/env python
"""
  Script to be load by each remote core, defining job to run
  on remote cores. 
"""
try:
   import cPickle as pickle
except:
   import pickle
import os, sys
import psutil, socket
import time, random
import numpy as np
# Custom modules
# This script is executed on remote cores,
# so we need to set system path on remote node.
sys.path.insert(0, './modules')
import job


def hostname():
    return socket.gethostname()

def working_dir():
    return os.getcwd()

def listdir(path):
    return os.listdir(path)

def pid(output_dir, arg, gateway_id):
    f = output_dir + '{}'.format(arg)
    with open(f, 'w') as wid:
        wid.write('arg: {}  node: {}  pid: {}'.format(
                   arg,
                   gateway_id.split('_')[0],
                   os.getpid()
                 ))
    return '-- remote PID: {}'.format(os.getpid())

def fac(arg):
    return np.math.factorial(arg)

def dump(output_dir, arg):
    f   = output_dir + 'fac_{}'.format(arg)
    t_0 = time.time()
    num = fac(arg)                             # Main operation
    t_1 = time.time()
    pickle.dump(num, open(f, "w"), protocol=2) # Main operation
    t_2 = time.time()
    duration_0 = "{:.4f}".format(t_1 - t_0)
    duration_1 = "{:.4f}".format(t_2 - t_1)
    return '-- Calculation: {} s, dumping: {} s'.format(
           duration_0, duration_1)


if __name__ == '__channelexec__':
    ''' Make sure the returned item from queue.get() is "ready"
        whenever the job is running. '''
    channel.send("ready")

    ''' In the following, 'arg' is sent by submit_jobs.py
        at position '# Submit a job.' '''
    for item in channel:
        if item is None:
            # Channel shutdown, will send back endmarker to master node.
            break
        elif len(item) == 3:
            output_dir, arg, gateway_id = item
            if str(arg).isdigit():
                # Send tasks to execute in remote nodes.
                # When task finishes, the corresponding results are
                # sent back to master node through the channel.
                channel.send((
                      str(arg)+' !',
                      job.pid(output_dir, arg, gateway_id),
                      job.dump(output_dir, arg)
                    ))
            else:
                print 'Firtst item sent should be an integer'
        else:
            print 'Warnning! arg sent should be [str, int, str] or None'
