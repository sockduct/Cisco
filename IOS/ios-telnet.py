#!/usr/bin/env python
####################################################################################################
'''
A script that connects to the specified IOS devices, logsin, and executes the specified command.
'''

# Future imports must be first
from __future__ import print_function

# Imports
import argparse
import datetime
import getpass
import os
from pprint import pprint
import socket
import sys
import telnetlib
import time
import yaml

# Globals
# Can be Username or username:
LOGIN_PROMPT = 'sername:'
# Can be Password or password
# Note - with CS-ACS, default is:
# * password = ACS in use
# * Password = Local-mode fallback
PASSWORD_PROMPT = 'assword:'
IOS_CMD = 'show ip ssh'
IOS_FILE = 'iosdevs.yaml'
IOS_NOPAGING = 'terminal length 0'
IOS_PROMPT = r'>|#'
TELNET_PORT = 23
TELNET_TIMEOUT = 6

# Metadata
__author__ = 'James R. Small'
__contact__ = 'james<dot>r<dot>small<at>outlook<dot>com'
__date__ = 'July 11, 2016'
__version__ = '0.0.3'


####################################################################################################
def yaml_input(file1, verbose=False):
    '''Read in router/switch authentication information from YAML file.'''
    data1 = {}

    if os.path.isfile(file1):
        with open(file1) as fh1:
            data1 = yaml.load(fh1)
        if verbose:
            print('Router data read from {}:'.format(file1))
            pprint(data1)
    else:
        # Don't output error if using default file name
        if verbose and file1 != IOS_FILE:
            print('Error:  Invalid filename {}'.format(file1))

    return data1

####################################################################################################
def check_input(router1, telnet_port, verbose=False):
    '''Validate router input data, prompt for anything missing.'''
    if 'device_type' not in router1:
        router1['device_type'] = raw_input('Router device type: ')
    if 'ip_addr' not in router1:
        router1['ip_addr'] = raw_input('Router IPv4 Address: ')
    if 'username' not in router1:
        router1['username'] = raw_input('Username for Router: ')
    if 'password' not in router1:
        router1['password'] = getpass()
    if 'port' not in router1:
        if verbose and not telnet_port:
            print('Telnet port not specified, using default of 23.  Override with -p option.')
        if not telnet_port:
            telnet_port = 23
        router1['port'] = telnet_port
    elif telnet_port:
        if verbose:
            print('overriding (telnet) port value ({}) with passed -p value ({})'.format(
                router1['port'], telnet_port))
        router1['port'] = telnet_port

####################################################################################################
class Router(object):
    '''A class to represent a Cisco IOS router'''

    def __init__(self, ip_addr, username, password, verbose=False):
        self.ip_addr = ip_addr
        self.username = username
        self.password = password
        self.verbose = verbose
        self.connection = telnetlib.Telnet()

    def _login(self):
        '''
        Login to network device
        '''
        output = self.connection.read_until(LOGIN_PROMPT, TELNET_TIMEOUT)
        if self.verbose:
            print('Node authentication banner:\n{}'.format(output))
            print('Logging in as {}...'.format(self.username))
        self.connection.write(self.username + '\n')
        output += self.connection.read_until(PASSWORD_PROMPT, TELNET_TIMEOUT)
        if self.verbose:
            # Skip first line, node echoing back username
            secondline = output.find('\n') + 1
            print('Node password prompt:\n{}'.format(output[secondline:]))
            print('Submitting password...')
        self.connection.write(self.password + '\n')
        
        post_login_prompt = [LOGIN_PROMPT, IOS_PROMPT]
        if self.verbose:
            print('Checking for successful login...')
        # We don't care about/use the match output from expect so assigned to '_'
        post_login_index, _, post_login_output = node_conn.expect(
            post_login_prompt, TELNET_TIMEOUT*2)
        if self.verbose:
            print('Post login output:\n{}'.format(post_login_output))
        if post_login_index == 0:
            # Don't exit, just print diagnostic to stderr
            #sys.exit('Authentication failed')
            print('Authentication failed', file=sys.stderr)
        else:
            if self.verbose:
                print('Authentication succeeded')

        return output

    def telnet_connect(self):
        '''
        Establish telnet connection
        '''
        try:
            if self.verbose:
                print('Trying {}...'.format(self.ip_addr))
            self.connection.open(self.ip_addr, TELNET_PORT, TELNET_TIMEOUT)
        except socket.timeout:
            # Don't exit, just print diagnostic to stderr
            #sys.exit('Connection to {} timed-out'.format(self.ip_addr))
            print('Connection to {} timed-out'.format(self.ip_addr), file=sys.stderr)
            self.connection = None
            return None

        # Login
        return self._login()

    def disable_paging(self, no_paging_cmd=IOS_NOPAGING):
        '''
        Disable the paging of output (i.e. --More--)
        '''
        return self.send_cmd(no_paging_cmd)

    def send_cmd(self, cmd):
        '''
        Send a command down the telnet channel

        Return the response
        '''
        # Sanity check
        if not self.connection:
            print('Error:  No connection exists.', file=sys.stderr)
            return None

        if self.verbose:
            print('Sending command {}...'.format(cmd))
        cmd = cmd.rstrip()
        self.connection.write(cmd + '\n')
        # Read until node prompt, this should indicate command output is done
        output = node_conn.read_until(IOS_PROMPT, TELNET_TIMEOUT)
        # Strip off last line - node prompt
        lastline = output.rfind('\n')
        cmd_output = output[:lastline]
        if verbose:
            print('Node output:\n{}'.format(cmd_output))
            print('Node prompt (omitted from output):  {}'.format(lastline))

        # Using prompt search instead of sleep delay
        #time.sleep(1)

        #return self.connection.read_very_eager()
        return cmd_output

def main(args):
    '''Acquire necessary input options, execute specified command on one or more routers,
    process per CLI args.'''
    # Benchmark
    prog_start = datetime.datetime.now()

    # Process CLI arguments
    parser = argparse.ArgumentParser(
        description='Execute show arp on specified routers')
    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument('-d', '--datafile', help='specify YAML file to read router info from',
                        default=IOS_FILE)
    parser.add_argument('-p', '--port', help='specify telnet port (default is 23)')
    parser.add_argument('--prompt', action='store_true',
                        help='prompt for router info (do not try to read in from file)',
                        default=False)
    parser.add_argument('-v', '--verbose', action='store_true', help='display verbose output',
                        default=False)
    args = parser.parse_args()

    # Debugging
    #print('Args:\n{}'.format(args))

    # Initialize data structures
    if not args.prompt:
        myrouters = yaml_input(args.datafile, args.verbose)
        if myrouters == {}:
            myrouters = [{}]
    else:
        myrouters = [{}]

    # Debugging
    #print('myrouters:\n{}'.format(myrouters))
    for router in myrouters:
        # Debugging
        #print('router:  {}'.format(router))
        check_input(router, args.port, args.verbose)

    for router in myrouters:
        # Debugging
        #print('router:  {}'.format(router))
        myrouter = Router(router['ip_addr'], router['username'], router['password'], args.verbose)
        # **router doesn't work with additional parameter afterwards
        #myrouter = Router(**router, args.verbose)
        myrouter.telnet_connect()
        myrouter.disable_paging()
        output = myrouter.send_cmd(IOS_CMD)
        # Make sure we have output
        if output:
            print('{} on [{}:{}]:\n{}\n'.format(IOS_CMD, router['ip_addr'], router['port'],
                  output))
        # Make sure we have a valid connection
        if myrouter.connection:
            myrouter.connection.close()

    # Benchmark
    print('\nBenchmarking:')
    print('Program start time:  {}'.format(prog_start))
    prog_end = datetime.datetime.now()
    print('Program end time:  {}'.format(prog_end))
    prog_time = prog_end - prog_start
    print('Elapsed time:  {}'.format(prog_time))


# Call main and put all logic there per best practices.
# No triple quotes here because not a function!
if __name__ == "__main__":
    # Recommended by Matt Harrison in Beginning Python Programming
    # sys.exit(main(sys.argv[1:]) or 0)
    # Simplied version recommended by Kirk Byers
    main(sys.argv[1:])


####################################################################################################
# Post coding
#
# pylint <script>.py
#   Score should be >= 8.0
#
# Future:
# * Testing - doctest/unittest/other
# * Logging
#
# To do:
# Incorporate techniques from telnet_pingsweep into class
#

