#!/usr/bin/env python
"""
  Use master mode to terminate jobs running on remote cores.
  It is sssumed that the sudo-passwords are the same on all remote nodes.
"""
import os, sys
import getpass
import glob, random
import time
import threading
# Custom modules
from . import paramikoSshClient


class backgroundProcess(threading.Thread):
    "A class to run a background process."

    def __init__(self, pw, work_dir, delta=10.0):
        self.pw       = pw
        self.work_dir = work_dir
        self.delta    = delta

        thread = threading.Thread(
                     target = self.terminate,
                     args   = ()
                 )
        thread.daemon = True  # Make thread background
        thread.start()

    def terminate(self):
        """ A process runing forever by itself. """
        while True:
            dump_file = check_status(self.work_dir)

            if dump_file:
                arg, node, pid = read_dump(dump_file)
                print '!!! {}! running on {} will be killed'.format(arg, node)
                ''' SSH to a worker node then terminate a job. '''
                client = paramikoSshClient.makeSshClient(
                             host     = node,
                             username = getpass.getuser(),
                             password = self.pw,
                             port     = 22
                         )
                response = client.execute(
                               'sudo kill -9 {}'.format(pid),
                                sudo = True
                           )
                if not response['err']:
                    print '    Process {} on node {} killed, {}!'.format(
                           pid, node, arg)
                    # Delete temporary dump file associated with this job.
                    os.remove(self.work_dir + '{}'.format(arg))
                else:
                    print '    Process {} not killed, error:\n{}'.format(
                           response['err'])
                sys.stdout.flush()
                client.close()

            time.sleep(self.delta)

def check_status(work_dir):
    ''' Function to check the calculated factorials and determine
        which running job should be terminated.
        In this demo code, we randomly take one of the running jobs
        as the one to terminate.
    '''
    # Check existing temporary dump files.
    # All dump files related to finished or killed jobs should
    # have been deleted.
    files = [f for f in glob.glob('{}*'.format(work_dir)) \
               if os.path.basename(f).isdigit()]
    if files:
        return files[ random.randint(0, len(files)-1) ]
    else:
        return None

def read_dump(f):
    ''' Read job information from dump file f. '''
    nodes, ncores = [], []
    with open(f, 'r') as fid:
        line = fid.readline().split()
    arg  = int(line[1])
    node = line[3]
    pid  = int(line[5])
    return arg, node, pid


if __name__ == '__main__':
    pw       = sys.argv[1]
    work_dir = '/home/mpiuser/test/'
    backgroundProcess(
        pw       = pw,
        work_dir = work_dir
    )
    time.sleep(30)
