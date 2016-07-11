# Possible improvements
# * Allow use of environment variables
# ** hostname, username, command sequence
# * Allow use of ssh keypair instead of password

# Imports
import argparse
import getpass
import paramiko
import time

def disable_paging(remote_conn):
    '''Disable paging on a Cisco router'''
    remotecon.send('terminal length 0\n')
    time.sleep(1)
    # Clear the buffer on the screen
    output = remotecon.recv(1000)
    return output

# Main
# Interactive only at this point so assuming main
#if __name__ == '__main__':
parser = argparse.ArgumentParser(description='execute single command on IOS device')
group = parser.add_mutually_exclusive_group()
group.add_argument('-v','--verbose',action='store_true')
group.add_argument('-q','--quiet',action='store_true')
parser.add_argument('-u','--user',help='username',required=True)
parser.add_argument('-p','--pswd',help='password')
parser.add_argument('host',help='hostname|address')
parser.add_argument('cmd',help='command sequence to execute on host')
args = parser.parse_args()

if args.quiet:
    verbose = 0
elif args.verbose:
    verbose = 2
else:
    verbose = 1

# Variables
# hostname|address - passed as argument
hostname = args.host
# username - passed as argument
username = args.user
# password - could be passed as argument, if not then prompt
password = args.pswd
if password == None:
    # Don't use raw_input, use getpass instead so don't echo password to terminal
    #password = raw_input('Password:')
    password = getpass.getpass('Password:  ')
# command sequence
cmdseq = args.cmd

# Instantiate ssh client object:
remoteconpre = paramiko.SSHClient()
# Automatically add host key (makes us susceptible to MITM)
remoteconpre.set_missing_host_key_policy(paramiko.AutoAddPolicy())
# Initiate ssh connection
remoteconpre.connect(hostname,username=username,password=password,look_for_keys=False,allow_agent=False)
print 'ssh connect established to %s' % hostname
# Start an interactive session
remotecon = remoteconpre.invoke_shell()
if verbose >= 2:
    print 'Interactive ssh session established'
# Strip initial router banner/prompt
rcoutput = remotecon.recv(1000)
if verbose >= 2:
    # Examine output
    print rcoutput
# Turn off paging
rcoutput = disable_paging(remotecon)
if verbose >= 2:
    # Examine output
    print rcoutput
# Send the router a command
remotecon.send('\n')
remotecon.send(cmdseq + '\n')
# Wait for command to complete
time.sleep(2)
rcoutput = remotecon.recv(5000)
print rcoutput

