#!/usr/bin/env python
####################################################################################################
#
# To do/improvements to look at:
# 1) Incorporate techniques from telnet_pingsweep into class
# 2) Add case where no password set:
#    telnet to netinfdev node and get:  Password required, but none set
# 3) Add option to check for ssh readiness:
# ** Need ip domain-name, RSA key pair (check modulus size), AAA or local user account, Available
#    vtys and vty transport input must have ssh in the list or be unset; device must support
#    crypto and may need a specific license/image
# 4) Add option to setup ssh (if possible), should have ability to specify everything required from
#    above list
# 5) Adjust timeout so deals with TACACS+ (CS ACS) timeouts and note this
#
####################################################################################################
'''
A script that connects to the specified IOS devices, logs-in, and executes the specified command.
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
IOS_AUTHNOTSETUP = 'password required, but none set'
IOS_CMD = 'show ip ssh'
IOS_NOPAGING = 'terminal length 0'
IOS_PROMPT = r'>|#'  # Assuming prompt consists of "A-Za-z0-9_-"
NETINFDEVS_FILE = 'netinfdevs.yaml'
NEWLINE = '\r'
TELNET_PORT = 23
TELNET_TIMEOUT = 6

# Metadata
__author__ = 'James R. Small'
__contact__ = 'james<dot>r<dot>small<at>outlook<dot>com'
__date__ = 'July 11, 2016'
__version__ = '0.0.6'


####################################################################################################
def yaml_input(file1, verbose=False):
    '''Read in netinfdev node authentication information from YAML file.'''
    data1 = {}

    if os.path.isfile(file1):
        with open(file1) as fh1:
            data1 = yaml.load(fh1)
        if verbose:
            print('Router data read from {}:'.format(file1))
            pprint(data1)
        return data1
    else:
        # Don't output error if using default file name
        if verbose and file1 != IOS_FILE:
            print('Error:  Invalid filename {}'.format(file1))

####################################################################################################
def check_input(netinfdev, telnet_port, verbose=False):
    '''Validate netinfdev node input data, prompt for anything missing.'''
    if 'DEVTYPE' not in netinfdev:
        netinfdev['DEVTYPE'] = raw_input('Router device type: ')
    if 'MGMTADDR4' not in netinfdev:
        netinfdev['MGMTADDR4'] = raw_input('Router IPv4 Address: ')
    if 'USERNAME' not in netinfdev:
        netinfdev['USERNAME'] = raw_input('Username for Router: ')
    if 'PASSWORD' not in netinfdev:
        netinfdev['PASSWORD'] = getpass()
    if 'TELNET_PORT' not in netinfdev:
        if verbose and not telnet_port:
            print('Telnet port not specified, using default of 23.  Override with -p option.')
        if not telnet_port:
            telnet_port = 23
        netinfdev['TELNET_PORT'] = telnet_port
    elif telnet_port:
        if verbose:
            print('overriding (telnet) port value ({}) with passed -p value ({})'.format(
                netinfdev['port'], telnet_port))
        netinfdev['port'] = telnet_port

####################################################################################################
class Netinfdev(object):
    '''A class to represent a Network Infrastructure Device.
       Typically this would be a router or switch, but other devices such as a firewall,
       load balancer (ADC), IDS/IPS, proxy or other gateway-type device may also work.

       Initially this is targeted at Cisco IOS routers and potentially Cisco IOS switches.

       netinfdev dictionary:  Items with a * are optional
       MGMTADDR4    = IPv4 address which can be used to manage device
       USERNAME     = administrative user name
       PASSWORD     = administrative password
       *CONNTYPE    = Connection type (e.g., *standard (normal telnet), reverse (reverse telnet))
       *DESCR       = Text description of network infrastructure device
       *DEVTYPE     = ios-rtr|ios-sw|other
       *HOSTNAME    = netinfdev hostname
       *SNMP_COMM   = SNMP Community String
       *SNMP_PORT   = UDP/161 by default or other specified port (UDP)
       *TELNET_PORT = TCP/23 by default or other specified port (TCP), probably needed for reverse
                      telnet
    '''

    #def __init__(self, ip_addr, username, password, verbose=False):
    def __init__(self, netinfdev, telnet_timeout=TELNET_TIMEOUT, verbose=False):
        #self.ip_addr = ip_addr
        #self.username = username
        #self.password = password
        self.netinfdev = netinfdev  # Dictionary which holds all relevant device data
        if 'USE_USERNAME' not in self.netinfdev:
            if 'USERNAME' in self.netinfdev:
                self.netinfdev['USE_USERNAME'] = True
            else:
                self.netinfdev['USE_USERNAME'] = False
        if 'USE_PASSWORD' not in self.netinfdev:
            if 'PASSWORD' in self.netinfdev:
                self.netinfdev['USE_PASSWORD'] = True
            else:
                self.netinfdev['USE_PASSWORD'] = False
        self.telnet_timeout = telnet_timeout
        self.verbose = verbose
        self.netconn = telnetlib.Telnet()
        if self.verbose:
            print('Object values:')
            print('netinfdev dictionary:\n{}'.format(self.netinfdev))
            print('telnet timeout:  {}'.format(self.telnet_timeout))
            print('verbose:  {}\n'.format(self.verbose))

    #def _login(self, verbose=False):
    def _login(self):
        '''Login to netinfdev node.'''
        if self.verbose:
            print('USE_USERNAME:  {}'.format(self.netinfdev['USE_USERNAME']))
            print('USE_PASSWORD:  {}'.format(self.netinfdev['USE_PASSWORD']))

        # Three cases which are not mutually exclusive:
        # 1) Expecting username prompt
        # 2) Expecting password prompt
        # 3) Not expecting either a username or password prompt

        # What about auto-sense - use expect with strings to look for user prompt, password prompt
        # or IOS_PROMPT (already logged in - e.g., open reverse telnet session)

        # Case 1 - Username Prompt
        if self.netinfdev['USE_USERNAME']:
            output = self.netconn.read_until(LOGIN_PROMPT, TELNET_TIMEOUT)
            if self.verbose:
                print('Logging in as {}...'.format(self.netinfdev['USERNAME']))
            self.netconn.write(self.netinfdev['USERNAME'] + NEWLINE)

        # Case 2 - Password Prompt
        if self.netinfdev['USE_PASSWORD']:
            output = self.netconn.read_until(PASSWORD_PROMPT, self.telnet_timeout)
            if self.verbose:
                # Skip first line, node echoing back username
                secondline = output.find('\n') + 1
                print('Node password prompt:\n{}'.format(output[secondline:]))
                print('Submitting password...')
            self.netconn.write(self.netinfdev['PASSWORD'] + NEWLINE)

        # Case 3 - Neither username nor password prompt expected
        #   Potential Problems:  For IOS devices, if some form of authentication is required
        #                        but nothing is setup (in many cases this is the default) then
        #                        upon connecting the device will return, "Password required,
        #                        but none set" and subsequently disconnect
        #   Handle implicitly - check for "IOS_AUTHNOTSETUP" string while looking for netinfdev
        #                       prompt.

        #if not self.netinfdev['USE_USERNAME'] and not self.netinfdev['USE_PASSWORD']:
        #    max_wait = TELNET_TIMEOUT
        #    output = ''
        #    while max_wait >= 0:
        #       # This is perhaps sloppy - should check for "reading" EOF, but couldn't
        #       # get it to work.  This works for now...
        #        try:
        #            buffer = self.netconn.read_very_eager()
        #       # Check for EOF (remote end closed connection)
        #       # Doesn't work if do it this way...
        #       #if buffer == '':
        #       #    break
        #            output += buffer
        #       # Sleep for 500 ms
        #            time.sleep(0.500)
        #            max_wait -= 0.500
        #        except EOFError:
        #            break

        if self.verbose:
            print('EOF:  {}'.format(self.netconn.eof))

        # Send a few Newlines in case its an open reverse telnet connection to get the netinfdev
        # to echo back a prompt
        ###self.netconn.write(NEWLINE + NEWLINE)

        # Need to read input for a few seconds and see if get EOF (see Potential Problems, case 3
        # above)
        output = self.netconn.read_until(IOS_PROMPT, TELNET_TIMEOUT)
        output = output.strip()
        errchk = output.lower()
        if self.netconn.eof and errchk == IOS_AUTHNOTSETUP:
            if self.verbose:
                print('Received:\n{}\n'.format(output))
                print('EOF:  {}'.format(self.netconn.eof))
            return None
        elif self.verbose:
            print('Output from node:\n{}\n'.format(output))
        # Check if prompt
        # Check for EOF
        # If neither then keep looping until TELNET_TIMEOUT time has passed then abort
        # connection with error...
        # Abort on purpose
        ###assert True == False
        #!!!#

        ### Redundant - remove
        #if self.verbose:
        #    print('Node authentication banner:\n{}'.format(output))
        #    print('Logging in as {}...'.format(self.username))
        #self.netconn.write(self.username + '\n')
        #output += self.netconn.read_until(PASSWORD_PROMPT, TELNET_TIMEOUT)
        #if self.verbose:
        #    # Skip first line, node echoing back username
        #    secondline = output.find('\n') + 1
        #    print('Node password prompt:\n{}'.format(output[secondline:]))
        #    print('Submitting password...')
        #self.netconn.write(self.password + '\n')
        
        ### Hangs because netinfdev is waiting for login info so this reads nothing...
        post_login_prompt = [LOGIN_PROMPT, PASSWORD_PROMPT, IOS_PROMPT]
        if self.verbose and self.netinfdev['USE_USERNAME'] or self.netinfdev['USE_PASSWORD']:
            print('Checking for successful login...')
        elif self.verbose:
            print('Checking for successful connection...')

        # We don't care about/use the match output from expect so assigned to '_'
        ###post_login_index, _, post_login_output = node_conn.expect(
        post_login_index, post_login_match, post_login_output = self.netconn.expect(
            post_login_prompt, TELNET_TIMEOUT)
        if self.verbose:
            print('Post login output:\n{}, {}, {}'.format(post_login_index, post_login_match,
                                                          post_login_output))
        if post_login_index == 0:
            # Don't exit, just print diagnostic to stderr
            #sys.exit('Authentication failed')
            print('Authentication failed', file=sys.stderr)
        else:
            if self.verbose and self.netinfdev['USE_USERNAME'] or self.netinfdev['USE_PASSWORD']:
                print('Authentication succeeded')
            # No authentication
            else:
                print('Successfully connected')

        return output

    def telnet_connect(self):
        '''
        Establish telnet connection
        '''
        try:
            if self.verbose:
                print('Trying {}...'.format(self.netinfdev['MGMTADDR4']))
            self.netconn.open(self.netinfdev['MGMTADDR4'], TELNET_PORT, TELNET_TIMEOUT)
        except socket.timeout:
            # Don't exit, just print diagnostic to stderr
            #sys.exit('Connection to {} timed-out'.format(self.ip_addr))
            print('Connection to {} timed-out'.format(self.netinfdev['MGMTADDR4']), file=sys.stderr)
            print("Please ensure you don't have a host-based firewall/IPS blocking telnet " +
                  "connections.", file=sys.stderr)
            self.netconn = None
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
        if not self.netconn:
            print('Error:  No connection exists.', file=sys.stderr)
            return None
        elif self.netconn.eof:
            print('Error:  Connection at EOF', file=sys.stderr)
            return None

        if self.verbose:
            print('Sending command {}...'.format(cmd))
        cmd = cmd.rstrip()
        self.netconn.write(cmd + '\n')
        # Read until node prompt, this should indicate command output is done
        ###output = node_conn.read_until(IOS_PROMPT, TELNET_TIMEOUT)
        output = self.netconn.read_until(IOS_PROMPT, TELNET_TIMEOUT)
        # Strip off last line - node prompt
        lastline = output.rfind('\n')
        cmd_output = output[:lastline]
        if self.verbose:
            print('Node output:\n{}'.format(cmd_output))
            print('Node prompt (omitted from output):  {}'.format(lastline))

        # Using prompt search instead of sleep delay
        #time.sleep(1)

        #return self.netconn.read_very_eager()
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
                        default=NETINFDEVS_FILE)
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
        mynetinfdevs = yaml_input(args.datafile, args.verbose)
        if mynetinfdevs == {}:
            mynetinfdevs = [{}]
    else:
        mynetinfdevs = [{}]

    # Debugging
    #print('mynetinfdevs:\n{}'.format(mynetinfdevs))
    for netinfdev in mynetinfdevs:
        # Debugging
        #print('netinfdev:  {}'.format(netinfdev))
        check_input(netinfdev, args.port, args.verbose)

    for netinfdev in mynetinfdevs:
        # Debugging
        #print('netinfdev:  {}'.format(netinfdev))
        ##mynetinfdev = Netinfdev(netinfdev['MGMTADDR4'], netinfdev['USERNAME'], netinfdev['PASSWORD'], args.verbose)
        #print('args.verbose:  {}'.format(args.verbose))
        mynetinfdev = Netinfdev(netinfdev, verbose=args.verbose)
        # **netinfdev doesn't work with additional parameter afterwards
        #mynetinfdev = Router(**netinfdev, args.verbose)
        mynetinfdev.telnet_connect()
        mynetinfdev.disable_paging()
        output = mynetinfdev.send_cmd(IOS_CMD)
        # Make sure we have output
        if output:
            print('{} on [{}:{}]:\n{}\n'.format(IOS_CMD, netinfdev['MGMTADDR4'], netinfdev['port'],
                  output))
        # Make sure we have a valid connection
        if mynetinfdev.netconn:
            mynetinfdev.netconn.close()

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

