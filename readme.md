# Prerequisites

To run this code, you need to modify the contents of cluster_core_info according to your own cluster. You should be able to passwordlessly SSH your remote nodes.

##### Modules:

&nbsp;&nbsp;&nbsp;&nbsp;execnet <br />
&nbsp;&nbsp;&nbsp;&nbsp;psutil <br />
&nbsp;&nbsp;&nbsp;&nbsp;paramiko <br />

# Objective

Two functionalities are implemented in this demo project: 
  * to automatically set up and submit jobs on remote cores.
  * to automatically force termination of random remote jobs and submit new jobs to keep all remote cores busy.

The scenario of related real-world problem is as follows. Suppose we can run parallel jobs on a cluster, where each job takes many CPU time to finish and dumps its result to a file on the Network File System (NFS). We can keep monitoring these result files to determine if some on-going jobs are not needed any more, such that keeping running them will be wasting resources. We thus need to terminate these jobs, free the related remote cores, and submit new jobs.

The above requirement is most easily handled by using a hybrid of python/bash programming and scheduler software (SLURM, TORQUE, etc.) However, what if no scheduler software is installed and configured on cluster? This demo project provides a solution with an almost-pure-python approach. 

[Note]

In this demo project, there is no communication between different jobs. 


# Method

The multiprocessing module is used to run X processes simultaneously on master node, where X is the total number of remote cores in the cluster. Each process uses the execnet module to establish a channel connecting the master node and a remote core, then submit a job to the remote core and keep monitoring the status of the job. Each job is to calculate the factorial of a large integer, and dump result in binary format on NFS.

A background process (using the threading module) is kept running on master node to periodically check the dumped files and pick out some random jobs to terminate. The selected remote job is terminated via bash command with the paramiko module. The termination of a remote job also closes the channel between master node and remote core. A new channel is then established to submit a new job, thus utilizing all available remote cores.

The reason of the above design is that, execnet uses static gateway group to establish multiple channels and submit jobs to remote cores, where each channel keeps its unique PID on the remote node, no matter how many different jobs are submitted through this channel. This feature fits well if we do not need to terminate any on-going jobs. However, if a channel is closed by its PID, the connection to that remote core is lost, and no more job can be submitted to that remote core while the gateway group lives (so the remote core will remain idle). Thus, I specify that a gateway group contains only one channel. So, either the job successfully completes or gets terminated, its gateway is closed, and a new gateway and a new channel is created with a new PID, this enables new job submission and job-termination.


# Code structure

. <br />
├── input <br />
├── cluster_core_info <br />
├── main.py <br />
└── modules/ <br />
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;├── __init__.py <br />
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;├── parser.py <br />
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;├── submit_single_job.py <br />
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;├── job.py <br />
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;├── terminate_job.py <br />
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;└── paramikoSshClient.py <br />

##### input:

Input file containing required parameters.

##### cluster_core_info:

File containing the information of remote nodes, including host name and the number of physical cores on the node.

##### main.py:

Script running on master node. It initializes input parameters, sets up background-checking-process, and runs up to X processes simultaneously.

##### modules/parser.py:

Script running on master node. It reads parameters from the input file.

##### modules/submit_single_job.py:

Script running on master node. It defines one process, which establishes a channel connecting the master node and a remote core, then submits a job to the remote core.

##### modules/job.py:

Script running on remote cores. It defines the actual calculations and dump result file on NFS.

##### modules/terminate_job.py:

Script running on master node. It defines a background process to periodically check result files and terminate some on-going remote jobs.

##### modules/paramikoSshClient.py:

Script running on master node. A class to handle SSH connection to remote cores.


# Example output

Usage:

    python main.py <sudo-password>

Screen output:

> Gateways generated with user [mpiuser] on remote cores:
> 
> Process 24748 running on master node, submitting 190000! to a remote core <br />
> Process 24749 running on master node, submitting 190001! to a remote core <br />
> Process 24750 running on master node, submitting 190002! to a remote core <br />
> Process 24751 running on master node, submitting 190003! to a remote core <br />
> Job:  190000!  submitted to gateway Slave1_1 <br />
> Job:  190001!  submitted to gateway Slave1_0 <br />
> Job:  190002!  submitted to gateway Slave2_0 <br />
> Job:  190003!  submitted to gateway Slave2_1 <br />
> !!! 190002! running on Slave2 will be killed <br />
> &nbsp;&nbsp;&nbsp;&nbsp;Process 9096 on node Slave2 killed, 190002! <br />
> &nbsp;&nbsp;&nbsp;&nbsp;Gateway closed: Slave2_0 <br />
> &nbsp;&nbsp;&nbsp;&nbsp;Process 24750 completed/killed on master node <br />
> &nbsp;&nbsp;&nbsp;&nbsp;Remote core Slave2-0 freed <br />
> Process 24764 running on master node, submitting 190004! to a remote core <br />
> Job:  190004!  submitted to gateway Slave2_0 <br />
> !!! 190004! running on Slave2 will be killed <br />
> &nbsp;&nbsp;&nbsp;&nbsp;Gateway closed: Slave2_0 <br />
> &nbsp;&nbsp;&nbsp;&nbsp;Process 9160 on node Slave2 killed, 190004! <br />
> Gateway Slave1_1 returned: <br />
> &nbsp;&nbsp;&nbsp;&nbsp;('190000 !', '-- remote PID: 2361', '-- Calculation: 20.4878 s, dumping: 0.0914 s') <br />
> Job:  190000!  submitted to gateway Slave1_1 <br />
> &nbsp;&nbsp;&nbsp;&nbsp;Gateway closed: Slave1_1 <br />
> Gateway Slave1_0 returned: <br />
> &nbsp;&nbsp;&nbsp;&nbsp;('190001 !', '-- remote PID: 2360', '-- Calculation: 20.4682 s, dumping: 0.1100 s') <br />
> Job:  190001!  submitted to gateway Slave1_0 <br />
> &nbsp;&nbsp;&nbsp;&nbsp;Gateway closed: Slave1_0 <br />
> Gateway Slave2_1 returned: <br />
> &nbsp;&nbsp;&nbsp;&nbsp;('190003 !', '-- remote PID: 9097', '-- Calculation: 20.6473 s, dumping: 0.0811 s') <br />
> Job:  190003!  submitted to gateway Slave2_1 <br />
> &nbsp;&nbsp;&nbsp;&nbsp;Gateway closed: Slave2_1 <br />
> &nbsp;&nbsp;&nbsp;&nbsp;Process 24764 completed/killed on master node <br />
> &nbsp;&nbsp;&nbsp;&nbsp;Remote core Slave2-0 freed <br />
> Process 24780 running on master node, submitting 190005! to a remote core <br />
> Job:  190005!  submitted to gateway Slave2_0 <br />
> &nbsp;&nbsp;&nbsp;&nbsp;Process 24748 completed/killed on master node <br />
> &nbsp;&nbsp;&nbsp;&nbsp;Remote core Slave1-1 freed <br />
> Process 24783 running on master node, submitting 190006! to a remote core <br />
> Job:  190006!  submitted to gateway Slave1_1 <br />
> &nbsp;&nbsp;&nbsp;&nbsp;Process 24749 completed/killed on master node <br />
> &nbsp;&nbsp;&nbsp;&nbsp;Remote core Slave1-0 freed <br />
> Process 24786 running on master node, submitting 190007! to a remote core <br />
> Job:  190007!  submitted to gateway Slave1_0 <br />
> !!! 190005! running on Slave2 will be killed <br />
> &nbsp;&nbsp;&nbsp;&nbsp;Gateway closed: Slave2_0 <br />
> &nbsp;&nbsp;&nbsp;&nbsp;Process 9224 on node Slave2 killed, 190005! <br />
> !!! 190006! running on Slave1 will be killed <br />
> &nbsp;&nbsp;&nbsp;&nbsp;Gateway closed: Slave1_1 <br />
> &nbsp;&nbsp;&nbsp;&nbsp;Process 2399 on node Slave1 killed, 190006! <br />
> Gateway Slave1_0 returned: <br />
> &nbsp;&nbsp;&nbsp;&nbsp;('190007 !', '-- remote PID: 2429', '-- Calculation: 20.5788 s, dumping: 0.1061 s') <br />
> Job:  190007!  submitted to gateway Slave1_0 <br />
> &nbsp;&nbsp;&nbsp;&nbsp;Gateway closed: Slave1_0
> 
> All jobs done.
