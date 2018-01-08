# Objective

Two functionalities are implemented in this demo project: 
  * to set up and submit jobs on remote cores.
  * to force termination of random remote jobs and submit new jobs to keep all remote cores busy.

The scenario of related real-world problem is as follows. Suppose we can run parallel jobs on a cluster, where each job takes many CPU time to finish and dumps its result to a file on the Network File System (NFS). We can keep monitoring these result files to determine if some on-going jobs are not needed any more, such that keeping running them will be wasting resources. We thus need to terminate these jobs, free the related remote cores, and submit new jobs.

The above requirement is most easily handled by using a hybrid of python/bash programming and scheduler software (SLURM, TORQUE, etc.) However, what if no scheduler software is installed and configured on cluster? This demo project provides a solution with an almost-pure-python approach. 

[Note]

In this demo project, there is no communication between different jobs. 


# Method

The multiprocessing module is used to run X processes simultaneously on master node, where X is the total number of remote cores in the cluster. Each process uses the execnet module to establish a channel connecting the master node and a remote core, then submit a job to the remote core and keep monitoring the status of the job. Each job is to calculate the factorial of a large integer, and dump result in binary format on NFS.

A background process (using the threading module) is kept running on master node to periodically check the dumped files and pick out some random jobs to terminate. The selected remote job is terminated via bash command with the paramiko module. The termination of a remote job also closes the channel between master node and remote core. A new channel is then established to submit a new job, thus utilizing all available remote cores.

The reason of the above design is that, execnet uses static gateway group to establish multiple channels and submit jobs to remote cores, where each channel keeps its unique PID on the remote node, no matter how many different jobs are submitted through this channel. This feature fits well if we do not need to terminate any on-going jobs. However, if a channel is closed by its PID, the connection to that remote core is lost, and no more job can be submitted to that remote core while the gateway group lives (so the remote core will remain idle). Thus, I specify that a gateway group contains only one channel. So, either the job successfully completes or gets terminated, its gateway is closed, and a new gateway and a new channel is created with a new PID, this enables both new job submission and job-termination.


# Code structure

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

input:

Input file containing required parameters.

cluster_core_info:

File containing the information of remote nodes, including host name and the number of physical cores on the node.

main.py:

Script running on master node. It initializes input parameters, sets up background-checking-process, and runs up to X processes simultaneously.

modules/parser.py:

Script running on master node. It reads parameters from the input file.

modules/submit_single_job.py:

Script running on master node. It defines one process, which establishes a channel connecting the master node and a remote core, then submits a job to the remote core.

modules/job.py:

Script running on remote cores. It defines the actual calculations and dump result file on NFS.

modules/terminate_job.py:

Script running on master node. It defines a background process to periodically check result files and terminate some on-going remote jobs.

modules/paramikoSshClient.py:

Script running on master node. A class to handle SSH connection to remote cores.


