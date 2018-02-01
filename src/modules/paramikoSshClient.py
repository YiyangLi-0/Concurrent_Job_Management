#!/usr/bin/python
'''
  Class to handle the SSH connection to remote cores.
  
  Codes are essentially taken from:
  https://stackoverflow.com/a/22592827/5831776
  https://gist.github.com/VEnis/6474534
'''
import sys
import paramiko
from StringIO import StringIO


class makeSshClient:
    "A wrapper of paramiko.SSHClient"
    TIMEOUT = 4.0

    def __init__(self, host, port, username, password,
                 key=None, passphrase=None):
        ''' Establish ssh connection. '''
        self.usr    = username
        self.pw     = password

        i, imax = 1, 3
        while True:
            sys.stdout.flush()
            try:
                self.client = paramiko.SSHClient()
                self.client.set_missing_host_key_policy(
                    paramiko.AutoAddPolicy()
                )
                if key is not None:
                    key = paramiko.RSAKey.from_private_key(
                              StringIO(key),
                              password=passphrase
                          )
                self.client.connect(
                    host, port,
                    username = username,
                    password = password,
                    pkey     = key,
                    timeout  = self.TIMEOUT
                )
                # Connected to host.
                break
            
            except paramiko.AuthenticationException:
                print "Authentication failed on {}.".format(host)
                sys.exit(1)
            
            except:
                # Could not connect to host, waiting to try again
                i += 1
                time.sleep(1.0)
        
            if i == imax:
                print "Could not connect to {}.".format(host)
                sys.exit(1)

    def close(self):
        ''' Close ssh connection. '''
        if self.client is not None:
            self.client.close()
            self.client = None

    def execute(self, cmd, sudo=False):
        ''' Execute cmd on a remote node via ssh. cmd is a string. '''
        feed_pw = False
        if sudo and self.usr != 'root':
            feed_pw = self.pw is not None and len(self.pw) > 0
            cmd     = "sudo -S -p '' {}".format(cmd)

        stdin, stdout, stderr = self.client.exec_command(cmd)
        
        if feed_pw:
            # Provide password using stdin.
            stdin.write(self.pw + "\n")
            stdin.flush()
        
        return {'out': stdout.readlines(), 
                'err': stderr.readlines(),
                'retval': stdout.channel.recv_exit_status()}


if __name__ == "__main__":
    client = makeSshClient(
                 host='host', port=22,
                 username='username', password='password'
             ) 
    try:
       ret = client.execute('dmesg', sudo=True)
       print "  ".join(ret['out']), "  E ".join(ret['err']), ret['retval']
    finally:
      client.close() 
