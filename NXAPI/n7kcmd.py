#!/usr/bin/env python
####################################################################################################
#
'''Example Python program to send commands to a Nexus 7000 using NX-API.

Future Improvements:
    * Use argparse to take CLI arguments/parameters
    * Create change function which is idempotent
    * Look at creating print function
    * Include examples/test cases:
    ** Setup VLAN
    ** Setup new loopback
    * Look into supporting object based rest change
    * Look into supporting authentication token vs. always posting username/password
    ** Need to deal with auth token expiring after 10 min
    ** Perhaps watch for auth token expiry and then re-do - make function or build-in to class?
    * Test cases such as invalid commands/operations
    * Need to clearly show case advantages of using NX-API vs. CLI
    ** Object based modeling & configuration
    ** Getting data perhaps not available through SNMP, using NX-API that wouldn't be easy to
       obtain via screen-scraping or CLI, especially if it's on dozens or hundreds of devices
    *** Spanning Tree changes/issues?
    ** Way to do transactional config across one or multiple devices
    ** Showcase deterministic configuration by leveraging error checking
'''


# Imports
import json
import requests
import sys

# Global Constants
N7K_ADDR4 = '198.18.1.77'
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
class NX_JRPC_OBJ(object):
    '''Representation of NX-API JSON-RPC Response Object'''

    def __init__(self, resp_dict):
        '''Setup Response Object'''
        self.version = resp_dict['jsonrpc']
        # Initialize result, error and id, set to None if not present
        # Note that only result or error will be present
        self.result = resp_dict.get('result')
        self.error = resp_dict.get('error')
        self.ident = resp_dict.get('id')

    def has_error(self):
        '''Response contains an error?'''
        # Error is None by default which == False
        if self.error:
            return True
        else:
            return False

    def get_error(self):
        '''Return error response'''
        # Error is None by default which == False
        if self.has_error():
            print json.dumps(self.error, sort_keys=True, indent=4)
        else:
            raise ValueError('Error not present in response object')

    def has_result(self):
        '''Response contains a result?'''
        # Result is None by default which == False
        if self.result:
            return True
        else:
            return False

    def get_result(self):
        '''Response contains a result?'''
        # Result is None by default which == False
        if self.has_result():
            print json.dumps(self.result['body'], sort_keys=True, indent=4)
        else:
            raise ValueError('Result not present in response object')

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

        # POST JSON-RPC request to N7K which results in returned response
        # Store returned response in a NX_JRPC_OBJ instance and return
        return NX_JRPC_OBJ(requests.post(myurl,
                                         data=json.dumps(payload),
                                         headers=NX_HEADER,
                                         auth=(self.username, self.password)
                                        ).json()
                          )

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

