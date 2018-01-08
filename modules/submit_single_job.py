#!/usr/bin/env python
"""
  Use master node to handle the submission of a single job to a remote core,
  and the managment of temporary dump files.
"""
import os, sys
import execnet
import re
# Custom modules
from . import job


def submit_job(label, arg, inp):
    ''' Establish objects to communicate calculations on remote cores. '''
    node, core = label.split('-')
    group, mch, queue = make_gateway(node, core, inp['work_dir'], inp['endmarker'])

    ''' Manage remote jobs. '''
    wid = open(inp['output_dir'] + 'finished_jobs_{}_{}'.format(
               inp['arg_lo'], inp['arg_hi']), 'a')
    while True:
        # Check the status of remote job.
        # 'item' is the current result sitting on the remote side of channel.
        channel, item = queue.get()

        sys.stdout.flush()
        if item == inp['endmarker']:
            # Channel terminated (either job-completion or user-temination).
            print "    Gateway closed: {}".format(channel.gateway.id)
            break

        if item != "ready":
            # A job completed on a remote core.
            print "    Gateway {} returned:\n    {}".format(
                  channel.gateway.id, item)
            mch.send_each(None)
            manage_dump_files(item, inp['output_dir'], wid)
        
        if arg:
            # Submit a job.
            # Sent term is copied by value to the remote side of channel.
            # May be blocked if the sender queue is full.
            channel.send( [inp['output_dir'], arg, channel.gateway.id] )
            print "Job:  {}!  submitted to gateway {}".format(
                   arg, channel.gateway.id)
    
    ''' Close the group of gateways. '''
    group.terminate()
    wid.close()

def make_gateway(node, core, work_dir, endmarker):
    ''' Generate a fixed-length (1) group of gateway groups for cores
        in remote nodes. Each gateway group contains a singel gateway,
        which can be terminated later, making room for a new gateway.
    '''
    def node_id(node):
        return re.findall(r'\d+', node)[0]

    group = execnet.Group()
    group.makegateway(
        "ssh={0}//id={0}_{1}//chdir={2}".format(
        node, core, work_dir
        ))

    mch   = group.remote_exec(job)
    queue = mch.make_receive_queue(endmarker = endmarker)
        # Either a channel is closed by job-completion (mch.send_each(None))
        # or by force-termination, the 2nd term of queue.get() is endmarker.
    return group, mch, queue

def manage_dump_files(item, output_dir, wid):
    ''' Manipulate dump files (written by function pid() in module job.py).
    '''
    finished_arg = item[0].split()[0]
    f = output_dir + '{}'.format(finished_arg)
    with open(f, 'r') as fid:
        line = fid.readline()
    # Delete temporary dump file associated with this finished job.
    os.remove(f)
    wid.write(line+'\n')


if __name__ == '__main__':
    pass
