#!/usr/bin/env python
####################################################################################################
#
# Improvements to look at:
# 1) Allow router data input from CLI
# 2) Spit out example router.yaml file
# 3) Use Python logging instead of printing to stdout
# 4) Allow more flexibility with command(s) to send to router/switch - from CLI, from file, or
#    default in script?
# 5) Consider command command menu like show run, show startup, show ip int brief, etc.
#
####################################################################################################
'''
Using telnetlib, connect to a device, iterate through a specified range of addresses and ping
each one.  Capture all the output in a specified log file.
'''

# Imports
import argparse
import netaddr
import os
from pprint import pprint
import socket
import sys
import telnetlib
import time
import yaml

# Globals
LOGIN_PROMPT = 'sername:'
NEWLINE = '\r'
PASSWORD_PROMPT = 'assword:'
ROUTER_CMD = 'ping'
ROUTER_FILE = 'router.yaml'
ROUTER_NOPAGING = 'terminal length 0'
ROUTER_PROMPT = r'>|#'
# Put in router.yaml file
#TELNET_PORT = 23
TELNET_TIMEOUT = 5

__version__ = '0.0.3'


def yaml_input(file1, verbose=False):
    '''Read in passwed file to obtain node authentication information.'''
    if os.path.isfile(file1):
        with open(file1) as f1:
            data1 = yaml.load(f1)
        if verbose:
            print 'Router data read from {}:'.format(file1)
            pprint(data1)
        return data1
    else:
        sys.exit('Invalid filename {}'.format(file1))

def last5(data):
    '''Given input data, return only the last 5 lines.'''
    endpos = -1
    for i in range(5):
        endpos = data.rfind('\n', 0, endpos)
    # +1 because endpos is on a newline, don't want the newline but
    # start at the character after
    return data[endpos + 1:]

####################################################################################################
class Netinfnode(object):
    '''A class to represent a network node - targeted at Cisco infrastructure routers and switches.
    '''

    def __init__(self, router, telnet_timeout):
        '''Initialize class data and setup place holder for socket connection.'''
        self.router = router
        self.telnet_timeout = telnet_timeout
        self.connection = telnetlib.Telnet()

    def _login(self, use_username=True, verbose=False):
        '''Login to node with username in router.'''
        if use_username:
            if verbose:
                print 'Logging in as {}...'.format(self.router['USERNAME'])
            self.connection.write(router['USERNAME'] + NEWLINE)

        # Password
        output = self.connection.read_until(PASSWORD_PROMPT, self.telnet_timeout)
        if verbose:
            # Skip first line, node echoing back username
            secondline = output.find('\n') + 1
            print 'Node password prompt:\n{}'.format(output[secondline:])
            print 'Submitting password...'
        self.connection.write(router['PASSWORD'] + NEWLINE)
    
        # Succeeded?
        post_login_prompt = [LOGIN_PROMPT, ROUTER_PROMPT]
        if verbose:
            print 'Checking for successful login...'
        # Don't care about match object from expect so using '_'
        post_login_index, _, post_login_output = self.connection.expect(
            post_login_prompt, self.telnet_timeout*2)
        if verbose:
            print 'Post login output:\n{}'.format(post_login_output)
        if post_login_index == 0:
            sys.exit('Authentication failed')
        else:
            if verbose:
                print 'Authentication succeeded'

    def connect(self, verbose=False):
        '''Connect to specified node, login and setup an active connection handle.'''
        try:
            if verbose:
                print 'Trying [{}]:{}...'.format(self.router['ADDRESS'],
                    self.router['TELNET_PORT'])
            else:
                # Noticed that if I don't output something (verbose mode), I need to
                # insert some delay - otherwise the script doesn't execute correctly.
                # It seems to "get ahead of itself" without the delay - not sure if
                # there's a better way to do this.  Note - I added many of these
                # delays - seem to need over a second total or script doesn't work.
                time.sleep(0.25)
            self.connection.open(self.router['ADDRESS'], self.router['TELNET_PORT'],
                self.telnet_timeout)
        except socket.timeout as e:
            sys.exit('Connection to {} timed out'.format(self.router['ADDRESS']))
        except socket.error as e:
            sys.exit('Connection error:  {}'.format(e))
    
        output = self.connection.read_very_eager()
        if verbose:
            print 'Node connection/authentication banner:\n{}'.format(output)
            print '------------------------------------------------------------------------'
        else:
            time.sleep(0.25)

        # Is this a reverse telnet-like connection (e.g., to a console/aux port)?
        if self.router['CONNECTION'] == 'ReverseTelnet':
            self.connection.write(NEWLINE)
            # Important to do this to clear remote device buffer
            output = self.connection.read_very_eager()
            if verbose:
                print 'Reverse Telnet-type connection, priming with newline...'
                # This could be screenfulls of output - just extract last 5 lines
                abridged_output = last5(output)
                print 'Last 5 lines received from device connection:\n{}'.format(abridged_output)
                print '------------------------------------------------------------------------'
            else:
                time.sleep(0.25)
    
        # Are we at a login prompt, a password prompt or a router/switch prompt?
        post_conn_prompt = [LOGIN_PROMPT, PASSWORD_PROMPT, ROUTER_PROMPT]
        if verbose:
            print 'Checking for connection state...'
        else:
            time.sleep(0.25)
        post_conn_index, _, post_conn_output = self.connection.expect(
            post_conn_prompt, self.telnet_timeout)
        if post_conn_index == 0:
            # At login prompt
            self._login(verbose=verbose)
        elif post_conn_index == 1:
            # At password prompt
            self._login(use_username=False, verbose=verbose)
        else:
            # At router/switch prompt - connection ready to go as is
            if verbose:
                print 'Router already at shell without authentication:\n{}'.format(
                    post_conn_output)
                print '------------------------------------------------------------------------'
            else:
                time.sleep(0.25)

    def nopaging(self, verbose=False):
        '''Disable paging on specified node.'''
        if verbose:
            print 'Disabling paging on node...'
        self.sendcmd(ROUTER_NOPAGING, verbose)
    
    def sendcmd(self, cmd, verbose=False):
        '''Execute passed command on specified node and return the output.'''
        # Normalize string by removing trailing whitespace (primarily \r or \n)
        cmd = cmd.rstrip()
        if verbose:
            print 'Sending command {}...'.format(cmd)
        self.connection.write(cmd + NEWLINE)
        #post_cmd_prompt = ['\n']
        # Read until newline sent back - this should be the node echoing back the command
        cmd_echo = self.connection.read_until('\n', self.telnet_timeout)
        #post_cmd_index, post_cmd_match, post_cmd_output = self.connection.expect(post_cmd_prompt,
        #        self.telnet_timeout)
        if verbose:
            #print 'Node echoes back:  {}'.format(post_cmd_output)
            print 'Node echoes back:  {}'.format(cmd_echo)
        post_cmd_prompt = [ROUTER_PROMPT]
        # Read until node prompt, this should indicate command output is done
        ## This doesn't appear to work:
        ##post_cmd_output = self.connection.read_until(ROUTER_PROMPT, self.telnet_timeout*4)
        # telnet_timeout * 4 to allow for long ping timeouts
        post_cmd_index, post_cmd_match, post_cmd_output = self.connection.expect(post_cmd_prompt,
                self.telnet_timeout*4)
        # Strip off last line - node prompt
        lastline = post_cmd_output.rfind('\n')
        cmd_output = post_cmd_output[:lastline]
        if verbose:
            print 'Node output:\n{}'.format(post_cmd_output)
    
        return cmd_output

def main(args):
    '''
    Obtain necessary input to execute ping sweep:
    telnet-pingsweep [--version] [-v|--verbose] [-f|--file <file.yaml>]
                     <starting-address-range> <ending-address-range>
    '''
    parser = argparse.ArgumentParser(description='Connect to a specified router and run a '
            'command')
    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument('-v', '--verbose', action='store_true', help='display verbose output',
            default=False)
    parser.add_argument('-f', '--file', help='specify YAML file to read router info from',
            default=ROUTER_FILE)
    parser.add_argument('-o', '--output', help='specify output file to write results to')
    parser.add_argument('addr_start', help='starting address for sweep')
    parser.add_argument('addr_end', help='ending address for sweep')
    args = parser.parse_args()

    # Pre-flight checks
    myrouter_data = yaml_input(args.file, args.verbose)

    # Validate IP addresses
    if netaddr.valid_ipv4(args.addr_start):
        addr_start = netaddr.IPAddress(args.addr_start)
    else:
        sys.exit('Invalid IPv4 address:  {}'.format(args.start))
    if netaddr.valid_ipv4(args.addr_end):
        addr_end = netaddr.IPAddress(args.addr_end)
    else:
        sys.exit('Invalid IPv4 address:  {}'.format(args.start))
    if addr_end <= addr_start:
        sys.exit('Ending address must be after starting address.')
    if (addr_end - addr_start).value > 254:
        sys.exit('Largest range of addresses which may be swept is limited to 254.')
    addr_range = netaddr.IPRange(addr_start, addr_end)

    myrouter = Netinfnode(myrouter_data, TELNET_TIMEOUT)
    myrouter.connect(args.verbose)
    myrouter.nopaging(args.verbose)
    if args.output:
        output1 = open(args.output, 'w')
    for addr in addr_range:
        full_cmd = ROUTER_CMD + ' ' + str(addr)
        print 'Processing {}...'.format(full_cmd)
        output = myrouter.sendcmd(full_cmd, args.verbose)
        # output has extra carriage returns - remove
        new_output = output.replace('\r', '')
        result = 'Command ({}) output:\n{}\n'.format(full_cmd, new_output)
        if args.output:
            output1.write(result)
            output1.write('\n')
        else:
            print result

    # Cleanup
    myrouter.connection.close()
    if args.output:
        output1.close()

# Call main and put all logic there per best practices.
# No comments below if because it's not a function!
####################################################################################################
if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]) or 0)

