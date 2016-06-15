#!/usr/bin/env python
####################################################################################################
#
'''Example Python program to send commands to a Nexus 7000 using NX-API.'''

# Imports
import json
import requests
import sys

# Global Constants
N7K_ADDR4 = '198.18.1.74'
NX_HEADER = {'content-type': 'application/json-rpc'}
NX_URL = '/ins'
NX_VER = 1.2
USERNAME = 'cisco'
# This is completely insecure - don't do this in production!
PASSWORD = 'cisco'
#
VLAN_ID = '101'
VLAN_NAME = 'Primary'

# Metadata
__author__ = 'James R. Small'
__contact__ = 'james<dot>r<dot>small<at>outlook<dot>com'
__date__ = 'June 14, 2016'
__version__ = '0.0.2'


####################################################################################################
class N7K(object):
    '''Representation of Nexus 7000'''

    # Class Variables - Global, not Instance specific
    xid = 0

    def __init__(self, mgmt_addr4, nxtrans, username, password):
        '''Setup N7k instance'''
        self.mgmt_addr4 = mgmt_addr4
        self.nxtrans = nxtrans
        self.username = username
        self.password = password
    
    def cmd(self, cmd1, verbose=False):
        '''Send command to a N7k instance'''
        # Increment xid
        N7K.xid += 1

        myurl = self.nxtrans + '://' + self.mgmt_addr4 + NX_URL
        payload = [{
            'jsonrpc': '2.0',
            'method': 'cli',
            'params': {
                'cmd': cmd1,
                'version': NX_VER
            },
            'id': N7K.xid
        }]
        if verbose:
            myrequest = requests.Request('POST', myurl, data=json.dumps(payload), \
                        headers=NX_HEADER, auth=(self.username, self.password))
            print '{}\n{}\n{}\n{}\n\n{}\n{}\n\n'.format(
                '-----------START-----------',
                myrequest.method + ' ' + myrequest.url,
                myrequest.auth,
                myrequest.headers,
                myrequest.data,
                '-----------END-----------')

        response = requests.post(myurl, data=json.dumps(payload), \
                   headers=NX_HEADER, auth=(self.username, self.password)).json()

        return response

####################################################################################################
def main(args):
    '''Define my Nexus 7000 switch and commands I want to send to it.'''
    myn7k = N7K(N7K_ADDR4, 'http', USERNAME, PASSWORD)

    # Execute one command and format output just for it:
    mycmd = 'show version'
    result = myn7k.cmd(mycmd)
    # Debugging
    #print 'Raw result:\n' + json.dumps(result, sort_keys=True, indent=4)
    if 'error' in result:
        result = result['error']
        print 'Error occurred.\nRequested command:  {}'.format(mycmd)
        print 'Error response:\n' + json.dumps(result, sort_keys=True, indent=4)
        sys.exit(-1)
    elif 'result' in result:
        result = result['result']
        result = result['body']

        print '{} result:\n{}'.format(mycmd, result['header_str'])
        for e in result:
            if e == 'header_str':
                pass
            else:
                print '{}:  {}'.format(e,result[e])
        print '\n'
    else:
        print 'Unexpected error - response contains neither result or error:'
        print json.dumps(result, sort_keys=True, indent=4)

    # Execute multiple commands and format output generically:
    commands = ['show ip int br', 'show ip route', 'show vlan', 'sh ip eigrp nei', 'sh int status']
    for mycmd in commands:
        result = myn7k.cmd(mycmd)

        if 'error' in result:
            result = result['error']
            print 'Error occurred.\nRequested command:  {}'.format(mycmd)
            print 'Error response:\n' + json.dumps(result, sort_keys=True, indent=4)
            sys.exit(-1)
        elif 'result' in result:
            result = result['result']
            result = result['body']
            print '{} result:\n'.format(mycmd)
            print json.dumps(result, sort_keys=True, indent=4)
            print '\n'
        else:
            print 'Unexpected error - response contains neither result or error:'
            print json.dumps(result, sort_keys=True, indent=4)

# Call main and put all logic there per best practices.
if __name__ == '__main__':
    main(sys.argv[1:])

