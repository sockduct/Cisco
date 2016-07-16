#!/usr/bin/env python
####################################################################################################
#
# This program uses Cisco's NX-API to communicate with a Nexus 7k
#
# Tested with NX-OSv v7.3(0)D1(1) on VIRL
#
# NX-API must be enabled on the Nexus 7k for this program to work:
# Enable NX-API:
# feature nxapi
#
# Enable NX-API Sandbox for testing (only in a lab/test environment):
# nxapi sandbox
# 
####################################################################################################
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

# Future Imports - Must be first:
# Use Python 3 style printing
from __future__ import print_function

# Imports
import json
import requests
import sys

# Global Constants
N7K_ADDR4 = ['198.18.1.78']
#N7K_ADDR4 = ['198.18.1.78', '198.18.1.79']
N7K_NAME = 'Nexus 7k'
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
__version__ = '0.0.3'


####################################################################################################
class NX_JRPC_OBJ(object):
    '''Representation of NX-API JSON-RPC Response Object'''

    def __init__(self, resp_dict):
        '''Setup Response Object'''
        self.version = resp_dict['jsonrpc']
        # Initialize result, error and id, set to None if not present
        # Note that only result or error will be present
        # Don't use get method default of None for results/errors because JSON can return Null
        # which is mapped to None!
        self.result = resp_dict.get('result', False)
        self.error = resp_dict.get('error', False)
        self.ident = resp_dict.get('id')

    def __repr__(self):
        '''Dump contents'''
        output = '[JSON Response]\n'
        output += '-' * 80 + '\n'
        output += 'JSON RPC Version:  {}\n'.format(self.version)
        if self.has_result():
            output += 'Result:\n'
            output += json.dumps(self.result, sort_keys=True, indent=4)
        else:
            output += 'Error:\n'
            output += json.dumps(self.error, sort_keys=True, indent=4)
        output += '\nIdentification#  {}\n'.format(self.ident)
        output += '-' * 80 + '\n'

        return output

    def has_error(self):
        '''Response contains an error?'''
        # * If no error is present, self.error == False
        # * It may be possible that self.error == None (Mapped from Null in JSON), not clear what
        #   this would mean but should report has_error as True because an error was returned
        # * Otherwise self.error will have some data and then the result is clearly True
        # Note:  None is a singleton, so use is None and not == None
        if self.error or self.error is None:
            return True
        else:
            return False

    def get_error(self):
        '''Return error response'''
        if self.has_error():
            #print json.dumps(self.error, sort_keys=True, indent=4)
            err_data_msg = ['msg', 'message']
            for key1 in ['code', 'data', 'message']:
                if key1 == 'data':
                    print('{}/{}:  {}'.format(key1, err_data_msg[1],
                          self.error[key1][err_data_msg[0]]), end='')
                else:
                    print('{:<7}:  {}'.format(key1, self.error[key1]))
        else:
            raise ValueError('Error not present in response object')

    def has_result(self):
        '''Response contains a result?'''
        # * If no result is present, self.result == False
        # * It may be possible that self.result == None (Mapped from Null in JSON), not clear what
        #   this would mean but should report has_result as True because an result was returned
        # * Otherwise self.result will have some data and then the result is clearly True
        # Note:  None is a singleton, so use is None and not == None
        if self.result or self.result is None:
            return True
        else:
            return False

    def get_result(self):
        '''Response contains a result?'''
        if self.has_result():
            #print json.dumps(self.result['body'], sort_keys=True, indent=4)
            if self.result:
                for key1, val1 in self.result['body'].items():
                    print('{}:  {}'.format(key1, val1))
            # Case where result is null which is mapped to None for Python
            # This isn't bad - some commands don't produce a result/output
            else:
                print('Null (No output)')
        else:
            raise ValueError('Result not present in response object')

####################################################################################################
class NX_JRPC_OBJs(object):
    '''Representation of NX-API JSON-RPC Response Object(s)'''

    def __init__(self, resp_obj):
        '''Setup Response Object'''
        self.resplst = []
        # Array of dictionaries
        if isinstance(resp_obj, list):
            for elmt in resp_obj:
                self.resplst.append(NX_JRPC_OBJ(elmt))
        # Individual response dictionary
        elif isinstance(resp_obj, dict):
            self.resplst.append(NX_JRPC_OBJ(dict))
        else:
            raise ValueError('Unexpected response type - {}'.format(type(resp_obj)))

    def __repr__(self):
        '''Dump contents'''
        output = '[JSON Response]\n'
        output += '-' * 80 + '\n'
        for indx, elmt in enumerate(self.resplst):
            output += '/' + '-' * 25 + '<' + str(indx) + '>' + '-' * 25 + '\\\n'
            output += 'JSON RPC Version:  {}\n'.format(elmt.version)
            if elmt.has_result():
                output += 'Result:\n'
                output += json.dumps(elmt.result, sort_keys=True, indent=4)
            else:
                output += 'Error:\n'
                output += json.dumps(elmt.error, sort_keys=True, indent=4)
            output += '\nIdentification#  {}\n'.format(elmt.ident)
            output += '\\' + '-' * 25 + '<' + str(indx) + '>' + '-' * 25 + '/\n'
        output += '-' * 80 + '\n'

        return output

    def no_errors(self):
        '''Response contains any errors?'''
        # * If no error is present, self.error == False
        # * It may be possible that self.error == None (Mapped from Null in JSON), not clear what
        #   this would mean but should report has_error as True because an error was returned
        # * Otherwise self.error will have some data and then the result is clearly True
        # Note:  None is a singleton, so use is None and not == None
        for elmt in self.resplst:
            if elmt.error or elmt.error is None:
                return False
        return True

    def has_errors(self):
        '''Response contains an error?'''
        # * If no error is present, self.error == False
        # * It may be possible that self.error == None (Mapped from Null in JSON), not clear what
        #   this would mean but should report has_error as True because an error was returned
        # * Otherwise self.error will have some data and then the result is clearly True
        # Note:  None is a singleton, so use is None and not == None
        for elmt in self.resplst:
            if elmt.error or elmt.error is None:
                return True
        return False

    def get_errors(self):
        '''Return error response'''
        for elmt in self.resplst:
            if elmt.has_error():
                #print json.dumps(elmt.error, sort_keys=True, indent=4)
                err_data_msg = ['msg', 'message']
                for key1 in ['code', 'data', 'message']:
                    if key1 == 'data':
                        print('{}/{}:  {}'.format(key1, err_data_msg[1],
                              elmt.error[key1][err_data_msg[0]]), end='')
                    else:
                        print('{:<7}:  {}'.format(key1, elmt.error[key1]))
            else:
                raise ValueError('Error not present in response object')

    def no_results(self):
        '''Response contains any results?'''
        # * If no result is present, self.result == False
        # * It may be possible that self.result == None (Mapped from Null in JSON), not clear what
        #   this would mean but should report has_result as True because an result was returned
        # * Otherwise self.result will have some data and then the result is clearly True
        # Note:  None is a singleton, so use is None and not == None
        for elmt in self.resplst:
            if elmt.result or elmt.result is None:
                return False
        return True

    def has_results(self):
        '''Response contains a result?'''
        # * If no result is present, self.result == False
        # * It may be possible that self.result == None (Mapped from Null in JSON), not clear what
        #   this would mean but should report has_result as True because an result was returned
        # * Otherwise self.result will have some data and then the result is clearly True
        # Note:  None is a singleton, so use is None and not == None
        for elmt in self.resplst:
            if elmt.result or elmt.result is None:
                return True
            else:
                return False

    def get_results(self):
        '''Response contains a result?'''
        for elmt in self.resplst:
            if elmt.has_result():
                #print json.dumps(elmt.result['body'], sort_keys=True, indent=4)
                for key1, val1 in elmt.result['body'].items():
                    print('{}:  {}'.format(key1, val1))
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
            print('{}\n{}\n{}\n{}\n{}\n{}\n{}\n'.format(
                  '[JSON Request]',
                  '-' * 80,
                  'HTTP Verb + URL :  ' + myrequest.method + ' ' + myrequest.url,
                  'HTTP Credentials:  ' + str(myrequest.auth),
                  'HTTP Header(s)  :  ' + str(myrequest.headers),
                  'HTTP JSON Data  :  ' + myrequest.data,
                  '-' * 80))

        # POST JSON-RPC request to N7K which results in returned response
        # Store returned response in a NX_JRPC_OBJ instance and return
        try:
            myresponse = NX_JRPC_OBJ(requests.post(myurl,
                                         data=json.dumps(payload),
                                         headers=NX_HEADER,
                                         auth=(self.username, self.password)
                                        ).json()
                                    )
        except requests.exceptions.ConnectionError as err1:
            print('Error connecting to {} at {}:'.format(N7K_NAME, self.mgmt_addr4))
            print('-' * 80)
            print(err1)
            print('-' * 80 + '\n')
            return None

        if verbose:
            #print('\n' + '-' * 80 + 'Raw result:\n' + json.dumps(result, sort_keys=True,
            #                                                     indent=4) + '-' * 80 + '\n')
            print(repr(myresponse))
        return myresponse

    def cmds(self, *cmds, **kwargs):
        '''Send one or more commands to a N7k instance'''
        if 'verbose' in kwargs:
            verbose = kwargs['verbose']
        else:
            verbose = False

        if verbose:
            print('kwargs = {}'.format(kwargs))
            print('cmds = {}'.format(cmds))

        # Overall setup:
        myurl = self.nxtrans + '://' + self.mgmt_addr4 + NX_URL
        payload = []

        for cmd in cmds:
            if verbose:
                print('cmd = {}'.format(cmd))

            # Increment xid
            N7K.xid += 1
    
            payload.append({
                'jsonrpc': '2.0',
                'method': 'cli',
                'params': {
                    'cmd': cmd,
                    'version': NX_VER
                },
                'id': N7K.xid
            })

        if verbose:
            myrequest = requests.Request('POST', myurl, data=json.dumps(payload), \
                        headers=NX_HEADER, auth=(self.username, self.password))
            print('\n{}\n{}\n{}\n{}\n{}\n{}\n{}\n'.format(
                  '[JSON Request]',
                  '-' * 80,
                  'HTTP Verb + URL :  ' + myrequest.method + ' ' + myrequest.url,
                  'HTTP Credentials:  ' + str(myrequest.auth),
                  'HTTP Header(s)  :  ' + str(myrequest.headers),
                  'HTTP JSON Data  :  ' + myrequest.data,
                  '-' * 80))

        # POST JSON-RPC request to N7K which results in returned response
        # Store returned response in a NX_JRPC_OBJ instance and return
        try:
            myresponse = NX_JRPC_OBJs(requests.post(myurl,
                                         data=json.dumps(payload),
                                         headers=NX_HEADER,
                                         auth=(self.username, self.password)
                                        ).json()
                                     )
        except requests.exceptions.ConnectionError as err1:
            print('Error connecting to {} at {}:'.format(N7K_NAME, self.mgmt_addr4))
            print('-' * 80)
            print(err1)
            print('-' * 80 + '\n')
            return None

        if verbose:
            #print('\n' + '-' * 80 + 'Raw result:\n' + json.dumps(result, sort_keys=True,
            #                                                     indent=4) + '-' * 80 + '\n')
            print(repr(myresponse))
        return myresponse

    def has_vlan(self, vlan_id, vlan_name=None, verbose=False):
        '''Check if VLAN present on N7k.
           If vlan_id exists and vlan_name passed, check if vlan_id's name matches vlan_name.
           If vlan_id exists (and vlan_id's name matches vlan_name if it was passed) return True
           Else return False
        '''
        cmd = 'show vlan'
        response = self.cmd(cmd, verbose)
        if response and response.has_result():
            myvlans = response.result['body']['TABLE_vlanbrief']['ROW_vlanbrief']
            if verbose:
                print('Passed VLAN ID   :  {}, type {}'.format(vlan_id, type(vlan_id)))
            for vlan in myvlans:
                if verbose:
                    print('Current VLAN ID  :  {}, type {}'.format(vlan['vlanshowbr-vlanid-utf'],
                                                              type(vlan['vlanshowbr-vlanid-utf'])))
                    print('Current VLAN Name:  {}, type {}'.format(vlan['vlanshowbr-vlanname'],
                                                              type(vlan['vlanshowbr-vlanname'])))
                if vlan['vlanshowbr-vlanid-utf'] == vlan_id:
                    if vlan_name and vlan['vlanshowbr-vlanname'] == vlan_name:
                        return True
                    elif not vlan_name:
                        return True
            return False
        else:
            return None

    def show_vlans(self):
        '''Show a list of all VLANs.'''
        cmd = 'show vlan'
        response = self.cmd(cmd)
        if response and response.has_result():
            myvlans = response.result['body']['TABLE_vlanbrief']['ROW_vlanbrief']
            output = 'VLAN ID    VLAN Name\n'
            output += '-------------------------------------------\n'
            for vlan in myvlans:
                output += '{:>5}      {}\n'.format(vlan['vlanshowbr-vlanid-utf'],
                                                    vlan['vlanshowbr-vlanname'])
            output += '-------------------------------------------\n'
            return output
        else:
            return None

    def set_vlan(self, vlan_id, vlan_name=None, verbose=False):
        '''Create/update VLAN ID and VLAN Name if necessary.
           If VLAN correctly setup, return False
           If VLAN needs to be setup and setup successfully, return True
           Else return None if error
        '''
        if not self.has_vlan(vlan_id, vlan_name, verbose):
            commands = ['configure terminal', 'vlan ' + str(vlan_id)]
            if vlan_name:
                commands.append('name ' + vlan_name)
            response = self.cmds(*commands, verbose=verbose)
            if response:
                return True
            else:
                return None
        else:
            return False

####################################################################################################
def main(args):
    '''Define my Nexus 7000 switch and commands I want to send to it.'''
    # Don't use http in production - this sends the username and password unencrypted!!!
    # \_Instead setup the Nexus box to support https
    myn7ks = []
    for n7k in N7K_ADDR4:
        myn7ks.append(N7K(n7k, 'http', USERNAME, PASSWORD))
    #myn7k = N7K(N7K_ADDR4, 'http', USERNAME, PASSWORD)

    # Execute multiple commands and format output generically:
    #commands = ['show version', 'invalid', 'show ip int br']
    commands = ['conf t']
    # and...:  ['show ip route', 'show vlan', 'sh ip eigrp nei', 'sh int status']
    for n7k in myn7ks:
        for cmd in commands:
            # Debugging/verbose output:
            #result = n7k.cmd(cmd, verbose=True)
            # verbose=False is the default
            #result = n7k.cmd(cmd, verbose=False)
            result = n7k.cmd(cmd)
            if result and not result.has_error():
                print('Command "{}" output for {} at {}:'.format(cmd, N7K_NAME, n7k.mgmt_addr4))
                print('-' * 80)
                result.get_result()
                print('-' * 80 + '\n')
            elif result:
                print('Sent command "{}" to {} at {} - error occurred:'.format(cmd, N7K_NAME,
                                                                               n7k.mgmt_addr4))
                print('-' * 80)
                result.get_error()
                print('-' * 80 + '\n')
            else:
                # Error occurred, nothing returned - error message should have been printed
                pass

        result = n7k.show_vlans()
        print('{} at {} VLANs:\n{}\n'.format(N7K_NAME, n7k.mgmt_addr4, result))

        # Test Cases:
        # Make sure VLAN 10 is created with the name "Example_Name" so this returns True
        myvlan_id = 10
        myvlan_name = 'Example_Name'
        result = n7k.has_vlan(myvlan_id, myvlan_name)
        print('{} at {} has VLAN {} - {}:  {}\n'.format(N7K_NAME, n7k.mgmt_addr4, myvlan_id,
                                                      myvlan_name, result))

        # Make sure VLAN 15 does not exist so this returns False
        myvlan_id = 15
        myvlan_name = 'DOESNT_EXIST'
        result = n7k.has_vlan(myvlan_id, myvlan_name)
        print('{} at {} has VLAN {} - {}:  {}\n'.format(N7K_NAME, n7k.mgmt_addr4, myvlan_id,
                                                      myvlan_name, result))

        # Make sure VLAN 20 exists but has a name different than "WRONG_NAME" so this returns
        # False
        myvlan_id = 20
        myvlan_name = 'WRONG_NAME'
        result = n7k.has_vlan(myvlan_id, myvlan_name)
        print('{} at {} has VLAN {} - {}:  {}\n'.format(N7K_NAME, n7k.mgmt_addr4, myvlan_id,
                                                      myvlan_name, result))

        # Make sure this VLAN doesn't exist so it's created and returns True
        myvlan_id = 30
        myvlan_name = 'Example_Thirty'
        result = n7k.set_vlan(myvlan_id, myvlan_name, verbose=False)
        print('{} at {} has VLAN {} - {}:  {}\n'.format(N7K_NAME, n7k.mgmt_addr4, myvlan_id,
                                                      myvlan_name, result))

# Call main and put all logic there per best practices.
if __name__ == '__main__':
    main(sys.argv[1:])

