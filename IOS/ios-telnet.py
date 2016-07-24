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
import ciscoconfparse
import datetime
import getpass
import os
from pprint import pprint
import re
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
IOS_AUTH_NOTSETUP = 'Password required, but none set'
IOS_CMD = 'show ip ssh'
IOS_ENABLE_NOTSETUP = '% No password set'
IOS_INPUT_ERR1 = '% Invalid input detected'
IOS_INPUT_ERR2 = '% Unknown command or computer name'
IOS_NOPAGING = 'terminal length 0'
# Assuming prompt consists of "A-Za-z0-9_-" and is limited to 63 characters as per Cisco hostname
# documentation - could vary with other platforms
IOS_CONF_PROMPT = r'[-\d\w()]{1,63}#'  
#IOS_GEN_PROMPT = r'\r\n[-\d\w()]{1,63}(#|>)'  
IOS_GEN_PROMPT = r'[-\d\w()]{1,63}(#|>)'  
IOS_PRIV_PROMPT = r'[-\d\w]{1,63}#'  
IOS_UNPRIV_PROMPT = r'[-\d\w]{1,63}>'  
NETINFDEVS_FILE = 'netinfdevs.yaml'
# For Python, should probably stick with '\n' - also what's shown in telnetlib example
#NEWLINE = '\r'
#LINETERM = '\r\n'
TELNET_PORT = 23
#TELNET_TIMEOUT = 6
TELNET_TIMEOUT = 10

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
        netinfdev['PASSWORD'] = getpass.getpass()
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
       ENABLE_PASS  = password to enter privileged mode
       *CONNTYPE    = Connection type (e.g., *standard (normal telnet), reverse (reverse telnet))
       *DESCR       = Text description of network infrastructure device
       *DEVTYPE     = ios-rtr|ios-sw|other
       *HOSTNAME    = netinfdev hostname
       *SNMP_COMM   = SNMP Community String
       *SNMP_PORT   = UDP/161 by default or other specified port (UDP)
       *TELNET_PORT = TCP/23 by default or other specified port (TCP), probably needed for reverse
                      telnet
    '''

    # Class Variables - Global, not Instance specific
    ios_conf_promptco = re.compile(IOS_CONF_PROMPT)
    ios_gen_promptco = re.compile(IOS_GEN_PROMPT)
    ios_priv_promptco = re.compile(IOS_PRIV_PROMPT)
    ios_unpriv_promptco = re.compile(IOS_UNPRIV_PROMPT)

    def __init__(self, netinfdev, telnet_timeout=TELNET_TIMEOUT, verbose=False):
        self.netinfdev = netinfdev  # Dictionary which holds all relevant device data
        self.config = None
        self.telnet_timeout = telnet_timeout
        self.verbose = verbose
        self.netconn = telnetlib.Telnet()
        if self.verbose:
            print('Object values:')
            print('netinfdev dictionary:\n{}'.format(self.netinfdev))
            print('telnet timeout:  {}'.format(self.telnet_timeout))
            print('verbose:  {}\n'.format(self.verbose))


    def _exitconfig(self):
        '''Attempt to exit configure mode on netinfdev node.'''
        if self.verbose:
            print('Attempting to exit configuration mode...')
        self.netconn.write('end' + '\n')

        # Node output cases after sending 'enable':
        # 0) echo back 'end'
        # 1) At privileged prompt
        # 2) Something else

        tries = 1
        node_prompts = ['end'+'\n', Netinfdev.ios_priv_promptco, '\n']

        while tries <= 3:
            # We don't care about/use the match output from expect so assigned to '_'
            node_prompt_index, _, node_prompt_output = self.netconn.expect(
                    node_prompts, TELNET_TIMEOUT)
            # Node echoing back 'end'
            if node_prompt_index == 0:
                if self.verbose:
                    print('Node echoing back end command:\n{}'.format(node_prompt_output))
            # At privileged password
            elif node_prompt_index == 1:
                if self.verbose:
                    print('Node at privileged prompt:\n{}'.format(node_prompt_output))
                break
            elif node_prompt_index == 2:
                if self.verbose:
                    print('Unexpected output:\n{}'.format(node_prompt_output))
            else:
                if self.verbose:
                    print('Node at unexpected shell prompt:\n{}'.format(node_prompt_output))
                # Try again...
            tries += 1

        # Still at/achieved shell access so return True (this is a pass through method)
        return True


    def _enable(self):
        '''Attempt to get privileged shell on netinfdev node.'''
        if self.verbose:
            print('Attempting to enter privileged mode...')
        self.netconn.write('enable' + '\n')

        # Node output cases after sending 'enable':
        # 0) echo back 'enable'
        # 1) At enable password prompt
        # 2) No enable password set (IOS_ENABLE_NOTSETUP)
        # 3) At unprivileged prompt
        # 4) At privileged prompt
        # 5) Something else

        enable_tries = 1
        enable_node_prompts = ['enable'+'\n', PASSWORD_PROMPT, IOS_ENABLE_NOTSETUP+'\n',
                               Netinfdev.ios_unpriv_promptco, Netinfdev.ios_priv_promptco, '\n']

        while enable_tries <= 4:
            # We don't care about/use the match output from expect so assigned to '_'
            node_prompt_index, _, node_prompt_output = self.netconn.expect(
                    enable_node_prompts, TELNET_TIMEOUT)
            # Node echoing back 'enable'
            if node_prompt_index == 0:
                if self.verbose:
                    print('Node echoing back enable command:\n{}'.format(node_prompt_output))
            # At enable password
            elif node_prompt_index == 1:
                if self.verbose:
                    print('Node at enable password prompt:\n{}'.format(node_prompt_output))
                if 'ENABLE_PASS' in self.netinfdev:
                    if self.verbose:
                        print('Submitting enable password...')
                    self.netconn.write(self.netinfdev['ENABLE_PASS'] + '\n')
                else:
                    if self.verbose:
                        print('Submitting user password as enable password...')
                    self.netconn.write(self.netinfdev['PASSWORD'] + '\n')
            # Enable password not set - can't enter enable mode
            elif node_prompt_index == 2:
                if self.verbose:
                    print('Node enable password not configured - cannot enter privileged ' +
                          'mode:\n{}'.format(node_prompt_output))
                break
            # Back at unprivileged prompt - something went wrong
            elif node_prompt_index == 3:
                if self.verbose:
                    print('Back at unprivileged shell prompt - something went wrong:\n' +
                          '{}'.format(node_prompt_output))
                # Try again...
            elif node_prompt_index == 4:
                if self.verbose:
                    print('Successfully entered privileged mode.')
                break
            elif node_prompt_index == 5:
                if self.verbose:
                    print('Unexpected output:\n{}'.format(node_prompt_output))
            else:
                if self.verbose:
                    print('Node at unexpected shell prompt:\n{}'.format(node_prompt_output))
                # Try again...
            enable_tries += 1

        # Still at/achieved shell access so return True (this is a pass through method)
        return True


    def _login(self):
        '''Login to netinfdev node.'''
        # Node shell prompt cases:
        # 0) At username prompt
        # 1) At password prompt
        # 2) At unprivileged prompt
        # 3) At privileged prompt
        # 4) At configuration prompt
        # 5) Authentication required but not setup (error - will be disconnected)

        # Note:  Sometimes parsing the prompt fails - probably want to retry once or twice

        # shell_level:
        # * 0 = False
        # * 1 = Unprivileged mode
        # * 2 = Privileged mode
        # * 3 = Configuration mode
        shell_level = 0
        at_shell = False
        used_username = False
        used_password = False
        shell_tries = 1
        node_prompts = [LOGIN_PROMPT, PASSWORD_PROMPT, Netinfdev.ios_unpriv_promptco,
                        Netinfdev.ios_priv_promptco, Netinfdev.ios_conf_promptco,
                        IOS_AUTH_NOTSETUP]
        if self.verbose:
            print('Checking device shell status...')

        # Note:  For reverse telnet connections, should use raw socket and send AO to flush
        #        remote output - can be screenfulls of it...
        # Something like:
        # sock = self.netconn.get_socket()
        # if sock is not None:
        #     sock.send(telnetlib.IAC + telnetlib.DO + telnetlib.AO)

        # Up to four passes through
        while not at_shell and shell_tries <= 4:
            # We don't care about/use the match output from expect so assigned to '_'
            node_prompt_index, _, node_prompt_output = self.netconn.expect(node_prompts,
                                                                           TELNET_TIMEOUT)
            # Login with username
            if node_prompt_index == 0:
                at_shell = False
                used_username = True
                if self.verbose:
                    print('Node at user login prompt:\n{}'.format(node_prompt_output))
                    print('Logging in as {}...'.format(self.netinfdev['USERNAME']))
                self.netconn.write(self.netinfdev['USERNAME'] + '\n')
            # Login with password
            elif node_prompt_index == 1:
                at_shell = False
                used_password = True
                if self.verbose:
                    print('Node at password login prompt:\n{}'.format(node_prompt_output))
                    # Skip first line, node echoing back username
                    #secondline = node_prompt_output.find('\n') + 1
                    #print('Node password prompt:\n{}'.format(node_prompt_output[secondline:]))
                    print('Node password prompt:\n{}'.format(node_prompt_output))
                    print('Submitting password...')
                self.netconn.write(self.netinfdev['PASSWORD'] + '\n')
            # In unprivileged mode
            elif node_prompt_index == 2:
                at_shell = True
                shell_level = 1
                if self.verbose:
                    print('Node at unprivileged shell prompt:\n{}'.format(node_prompt_output))
            # In privileged mode
            elif node_prompt_index == 3:
                at_shell = True
                shell_level = 2
                if self.verbose:
                    print('Node at privileged shell prompt:\n{}'.format(node_prompt_output))
            # In configuration mode
            elif node_prompt_index == 4:
                at_shell = True
                shell_level = 3
                if self.verbose:
                    print('Node at configuration shell prompt:\n{}'.format(node_prompt_output))
            elif node_prompt_index == 5:
                at_shell = False
                if self.verbose:
                    print("Node requires authentication but it isn't configured - node aborted " +
                          'connection.')
                # Abort...
                return None
            else:
                at_shell = False
                # Not sure what best way to retry is or if there are cases where we should just
                # abort
                if self.verbose:
                    print('Node at unexpected shell prompt:\n{}'.format(node_prompt_output))
                # Try again...
            # Increment counter
            shell_tries += 1

        if not at_shell:
            print('Authentication failed', file=sys.stderr)
            return None
        elif at_shell and shell_level == 1:
            # Try for privileged mode
            return self._enable()
        elif at_shell and shell_level == 2:
            if self.verbose and used_username or used_password:
                print('Authentication succeeded')
            # No authentication
            else:
                print('Successfully connected')
        elif at_shell and shell_level == 3:
            print('Warning - in configuration mode.', file=sys.stderr)
            return self._exitconfig()

        # Send a few Newlines in case its an open reverse telnet connection to get the netinfdev
        # to echo back a prompt
        ###self.netconn.write('\n' + '\n')

        return True


    def telnet_connect(self):
        '''
        Establish telnet connection
        '''
        try:
            if self.verbose:
                print('Trying {}:{}...'.format(self.netinfdev['MGMTADDR4'],
                                               self.netinfdev['TELNET_PORT']))
            self.netconn.open(self.netinfdev['MGMTADDR4'], self.netinfdev['TELNET_PORT'],
                              TELNET_TIMEOUT)
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
        '''Disable the paging of output (i.e. --More--).'''
        return self.send_cmd(no_paging_cmd)


    def send_cmd(self, cmd, timeout=TELNET_TIMEOUT):
        '''Send a command down the telnet channel
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
        node_prompt_index, _, output = self.netconn.expect([Netinfdev.ios_gen_promptco], timeout)
        if node_prompt_index != 0:
            if self.verbose:
                print('Failed to find prompt after executing command.  Output received:\n' +
                      '{}'.format(output))
            return None
        # Find first line - node echoing back command
        firstline = output.find('\n')
        # Find last line - node prompt
        lastline = output.rfind('\n')
        # Strip off first and last lines:
        cmd_output = output[firstline+1:lastline]
        if self.verbose:
            print('Node full output:\n{}'.format(output))

        return cmd_output


    def get_conf(self):
        '''Get running-config and return.'''
        output = self.send_cmd('show running-config', 60)
        # Remove "Building configuration..."
        secondline = output.find('\n')
        self.config = output[secondline+1:]
        if self.config:
            return True
        else:
            return False


    def check_ssh(self):
        '''Check if ssh is enabled on a node.
           If not, check what's missing:
           hostname <hostname>
           ip domain-name <domain>
           -or-
           ip domain name <domain>
           aaa authentication:
             aaa new-model
             aaa authentication login default <source>
             -or-
             aaa authentication login <named> <source>
             line vty 0
              login authentication <named>
           -or-
           local authentication:
            At least one username
            line vty 0
             login local
           Must allow inbound ssh:
            line vty 0
             transport input ssh
             -or-
             transport input all
           crypto image
            test:  crypto key generate rsa modulus 1024
        ''' 
        if not self.config:
            self.get_conf()

        # ciscoconfparse can only deal with config when each line is an item in a list
        conf_lst = self.config.split('\r\n')
        mycfg = ciscoconfparse.CiscoConfParse(conf_lst)
        if len(mycfg.find_lines(r'^hostname')) != 1:
            print('hostname not configured')
        if len(mycfg.find_lines(r'^ip (domain-name|domain name)')) != 1:
            print('ip domain name not configured')
        # Determine if local auth or central auth
        # If find aaa new-model, look at/for aaa setup
        # Note:  There are almost endless permutations - just looking for most common cases
        if len(mycfg.find_lines(r'^aaa new-model')) == 1:
            central_auth = False
            local_auth = False
            if len(mycfg.find_lines(r'^aaa authentication login default group')) >= 1:
                central_auth = True
            if not central_auth and len(mycfg.find_lines(
                    r'^aaa authentication login default local')) >= 1:
                local_auth = True
                if len(mycfg.find_lines(r'^username')) < 1:
                    print('Aaa mode configured for local users but none found')
            if not central_auth and not local_auth:
                print('Aaa mode enabled, but valid aaa authentication login default ' +
                      'configuration not found')
            # It is also possible to do a named aaa login authentication method
            # However, this is not as common and is thus not currently setup
        # Otherwise, just look for local setup
        else:
            if len(mycfg.find_lines(r'^username')) < 1:
                print('Non-aaa mode and no local users configured')
            vtycfg = mycfg.find_objects(r'^line vty 0')
            # Check for local login
            local_login = False
            for elmt in vtycfg[0].children:
                if elmt.text.find(' login local') == 0:
                    local_login = True
                    break
            if not local_login:
                print('line vty 0 not configured for local login')
            # Check that ssh is allowed input transport
            ssh_in_ok = False
            for elmt in vtycfg[0].children:
                if elmt.text.find(' transport input all') == 0:
                    ssh_in_ok = True
                    break
                if re.match(r'^ transport input .*ssh', elmt.text):
                    ssh_in_ok = True
                    break
            if not ssh_in_ok:
                print('ssh not allowed as input transport on line vty 0')

        # Check if ssh setup
        output = self.send_cmd('show ip ssh')
        ssh_on = output.find('SSH Enabled')
        if ssh_on == -1:
            print('ssh not enabled')


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
        mynetinfdev = Netinfdev(netinfdev, verbose=args.verbose)
        # **netinfdev doesn't work with additional parameter afterwards
        #mynetinfdev = Router(**netinfdev, args.verbose)
        result = mynetinfdev.telnet_connect()
        if result is None:
            continue
        mynetinfdev.disable_paging()
        output = mynetinfdev.send_cmd(IOS_CMD)
        # Make sure we have output
        if output:
            print('{} on [{}:{}]:\n{}\n'.format(IOS_CMD, netinfdev['MGMTADDR4'],
                  netinfdev['TELNET_PORT'], output))

        # Get running configuration
        #print(mynetinfdev.get_conf())

        # Check ssh
        mynetinfdev.check_ssh()

        # Make sure we have a valid connection
        if mynetinfdev.netconn:
            mynetinfdev.netconn.close()

    # Benchmark
    #print('\nBenchmarking:')
    #print('Program start time:  {}'.format(prog_start))
    #prog_end = datetime.datetime.now()
    #print('Program end time:  {}'.format(prog_end))
    #prog_time = prog_end - prog_start
    #print('Elapsed time:  {}'.format(prog_time))


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

