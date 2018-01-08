#!/usr/bin/env python
"""
  Use master mode to manage the submission of termination of jobs
  running on remote cores.

  Usage:
  0. Make sure that source scripts can be accessed by master and
     worker nodes through Network File System (NFS).
  1. ./main.py <sudo-password>
     It is assumed that sudo passwords are the same on all worker nodes.
"""
import os, sys
import multiprocessing, execnet
import psutil, getpass
import time
# Custom modules
from modules import parser
from modules import terminate_job
from modules import submit_single_job


def main():
    ''' Initialization. '''
    # Generate input dictionary inp.
    # For safty concern, password is not revealed in 'input' file.
    inp = parser.parser('input', sys.argv[1])

    check_output_dir(inp['output_dir'])
    clean_old_output(inp['output_dir'], inp['arg_lo'], inp['arg_hi'])

    ecexnet_location()
    usr = user()

    cluster= get_cluster_info(inp['core_info'])
    nrc = len(cluster)  # number of remote cores

    ''' Submit a background process on master node to check dump files
        and terminate some remote job, periodcially. '''
    terminate_job.backgroundProcess(
        pw       = inp['pw'],
        work_dir = inp['output_dir'],
        delta    = inp['check_delta']
    )

    ''' Submit up to nrc processes on master node, where each process
        uses execnet to send a job to run on a remote core. '''
    args = range(inp['arg_lo'], inp['arg_hi']+1)

    for i, arg in enumerate(args):
        if num_active_cores(cluster) < nrc:
            ''' Submit a new process on master node. '''
            run_process(arg, cluster, inp, submit_single_job)

        else:
            ''' Wait for a process to complete/terminate on master node. '''
            wait_process(num_active_cores, cluster, nrc, inp['run_delta'])

            ''' Submit a new process on master node. '''
            run_process(arg, cluster, inp, submit_single_job)

    final_output(terminate_job, inp['output_dir'], inp['run_delta'])


def check_output_dir(output_dir):
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

def clean_old_output(output_dir, lo, hi):
    old_file = output_dir + 'finished_jobs_{}_{}'.format(lo, hi)
    if os.path.exists(old_file):
        os.remove(old_file)

def ecexnet_location():
    print '  execnet source files are located at:\n  {}/\n'.format(
          os.path.join(os.path.dirname(execnet.__file__))
          )

def user():
    usr = getpass.getuser()
    print 'Gateways generated with user [{}] on remote cores:\n'.format(usr)
    return usr

def get_cluster_info(file):
    cluster = {}
    with open(file, 'r') as fid:
        while True:
            line = fid.readline()
            if not line:
                break
            node, ncore = line.split()
            for i in range(int(ncore)):
                cluster['{}-{}'.format(node,i)] = {'arg': None, 'proc': None}
    return cluster

def num_active_cores(cluster):
    ''' Return the number of occupied remote cores. '''
    return sum([1 for _, val in cluster.items() if val['arg'] != None])

def pick_free_core(cluster):
    ''' Return the dict-key of an unoccupied remote core. '''
    for key, val in cluster.items():
        if val['arg'] == None:
            break
    return key

def run_process(arg, cluster, inp, submit_single_job):
    ''' Run one process on master node. '''
    # Setup master node process p, which submits a job to a remote core.
    label = pick_free_core(cluster)
    cluster[label]['arg'] = arg

    p = multiprocessing.Process(
          name   = '{}'.format(arg),
          target = submit_single_job.submit_job,
          args   = (label, arg, inp)
        )

    # Run process p on master node.
    p.start()
    cluster[label]['proc'] = p

    # Output.
    s  = 'Process {} running on master node,'
    s += ' submitting {}! to a remote core'
    print s.format(p.pid, p.name)
    sys.stdout.flush()

def wait_process(num_active_cores, cluster, nrc, delta):
    ''' Wait for a process to complete/terminate on master node. '''
    while num_active_cores(cluster) == nrc:
        # Loop over all active processes and check status.
        for k, v in cluster.items():
            time.sleep(delta)
            if v['proc'].exitcode is None:
                # Current process still running, check next one.
                continue
            else:
                print '    Process {} completed/killed on master node'.format(
                       v['proc'].pid)
                v['proc'].join()  # Tidy up process.
            print '    Remote core {} freed'.format(k)
            sys.stdout.flush()
            # Reset status of this remote core to available.
            v['arg'], v['proc'] = None, None
            break

def final_output(terminate_job, output_dir, delta):
    while True:
        if terminate_job.check_status(output_dir):
            time.sleep(delta)
        else:
            print '\nAll jobs done.'
            break


if __name__ == '__main__':
    main()
