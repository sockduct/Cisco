#!/usr/bin/env python
####################################################################################################
'''Parse output from telnet-pingsweep.py and provide info/stats.'''

# Imports
# Delete unused lines/comments!
import argparse
import os
import re
import sys
import yaml

# Globals
IPv4_ADDR = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'
YAML_BOF = '---\n'

# Metadata
__author__ = 'James R. Small'
__contact__ = 'james<dot>r<dot>small<at>outlook<dot>com'
__date__ = 'April 25, 2016'
__version__ = '0.0.1'


def yaml_output(list1, outfile1, abroutform=True):
    '''Output passed list to passed file in YAML format.'''
    with open(outfile1, 'w') as file1:
        file1.write(YAML_BOF)
        file1.write(yaml.dump(list1, default_flow_style=abroutform))

def process_file(file1, verbose=0):
    '''Process file - glean info/stats'''
    content = file1.readlines()
    live_addr = []

    for line in content:
        # Remove newlines:
        line = line.rstrip()
        if verbose >= 2:
            print 'Parsing line:  {}'.format(line)
        if re.search(r'^Command', line):
            pass
        elif re.search(r'escape sequence', line):
            pass
        elif re.search(r'^Sending', line):
            result = re.findall(IPv4_ADDR, line)
            if len(result) != 1:
                sys.exit('Error - failed to parse out address from send_line')
            addr = result[0]
        elif re.search(r'[.!]{5}', line):
            if line.find('!') >= 0:
                # Found node responding to ping - save
                if verbose >= 1:
                    print 'Found live address:  {}'.format(addr)
                live_addr.append(addr)
        elif re.search(r'^Success rate', line):
            pass
        elif line == '':
            pass
        else:
            sys.exit('Error - unexpected line in file')

    return live_addr

def main(args):
    '''Acquire necessary input options, process file data, present info/stats.'''
    parser = argparse.ArgumentParser(
        description='Parse specified output file from telnet-pingsweep.py and present info/stats')
    parser.add_argument('--version', action='version', version=__version__)
    parser.add_argument('-v', '--verbose', help='increase output verbosity', action='count',
                        default=0)
    parser.add_argument('file', help='specify data file to read info from')
    args = parser.parse_args()

    with open(args.file) as infile:
        live_addr_list = process_file(infile, args.verbose)

    base_filename = os.path.splitext(args.file)[0]
    outfile = base_filename + '.yaml'
    if args.verbose >= 1:
        print 'Found {} live addresses.'.format(len(live_addr_list))
        print 'Writing list of live addresses to {}:\n{}'.format(outfile, live_addr_list)
    yaml_output(live_addr_list, outfile)

# Call main and put all logic there per best practices.
# No triple quotes here because not a function!
if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]) or 0)


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
