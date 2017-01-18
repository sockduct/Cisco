#!/usr/bin/env python
# -*- coding: ascii -*-
# Default is ascii - explicitly coding, could also consider utf-8, latin-1, cp1252, ...
####################################################################################################
#
# Python version(s) used/tested:
# * Python 2.7.11 on Windows
#
# Template version used:  0.1.0
#
#---------------------------------------------------------------------------------------------------
#
# Issues/PLanned Improvements:
# * <first>
# * <second>...
#
'''Cisco ASA Syslog Retrieval Tool
   * Get syslog documentation
   * Parse out syslog messages
   * Put into format importable into Microsoft Excel
'''

# Future Imports - Must be first, provides Python 2/3 interoperability
from __future__ import print_function       # print(<strings...>, file=sys.stdout, end='\n')
from __future__ import division             # 3/2 == 1.5, 3//2 == 1
from __future__ import absolute_import      # prevent implicit relative imports in v2.x
# This one more risky...
from __future__ import unicode_literals     # all string literals treated as unicode strings

# Imports
import csv
import re
import sys
# Third party libraries
import bs4
import requests

# Globals
# Note:  Consider using function/class/method default parameters instead of global constants where
# it makes sense
#BASE_FILE = 'file1'
ACCEPT = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
ASAHDR = ('Platform', 'Severity', 'Group', 'Number', 'Log Message')
ASALOG = '%ASA'
OUTFILE = 'asa-syslogs.csv'
SYSLOG_DOC = 'www.cisco.com/c/en/us/td/docs/security/asa/syslog-guide/syslogs/logsevp.html'
TIMEOUT = 10
URI = 'http://'
USERAGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.85 Safari/537.36'

# Metadata
__author__ = 'James R. Small'
__contact__ = 'james<dot>r<dot>small<at>outlook<dot>com'
__date__ = 'January 13, 2017'
__version__ = '0.0.1'


####################################################################################################
# Retrieve Passed Web Page (and deal with common problems) using requests
####################################################################################################
# For environments using a proxy:
#     HTTP_PROXY=http://19.12.1.140:83
#     HTTPS_PROXY=http://19.12.1.140:83
# Note:  Authentication is not accounted for in this example
####################################################################################################
#
# @param url Site, path and file to attempt to retrieve
# @param headers Headers to use within HTTP for web request
# @param verbose Output extra information if True
#
def getpage(url, headers=None, verbose=False):
    '''retrieve web page from <url> using <headers>'''
    session = requests.Session()
    try:
        if verbose:
            print('Retrieving data from {}...'.format(url))
        resp = session.get(url, headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
    except requests.exceptions.HTTPError as error:
        print('Client request or Server response error:\n{}'.format(error))
        sys.exit(-1)
    except requests.exceptions.ConnectionError as error:
        print('Connection error:\n{}'.format(error))
        sys.exit(-2)
    except requests.exceptions.ReadTimeout as error:
        print('Timeout waiting for server response:\n{}'.format(error))
        sys.exit(-3)
    except KeyboardInterrupt as error:
        print('Detected keyboard interrupt, aborting...\n{}'.format(error))
        sys.exit(-4)
    #
    return resp

####################################################################################################
# Scrape syslog documentation page (retrieve with getpage above, parse with beautiful soup
####################################################################################################
#
# @param resp Web page response containing syslog data
# @param verbose Output extra information if True
#
def scrapedoc(resp, verbose=False):
    '''Scrape relevant information from syslog documentation page and return it.'''
    syslog_data = []
    repat1 = r'^\d{6}:'
    repat2 = r'^\d{6} '
    repat3 = r'^\d{6}%:'
    repat4 = r'^[\dn]{6}:'

    soup = bs4.BeautifulSoup(resp.text, 'html.parser')
    data = soup.find_all('li')

    for i, line in enumerate(data):
        linedata = line.contents[-1]
        if isinstance(linedata, bs4.element.NavigableString):
            if linedata.startswith(ASALOG):
                # Note:  Windows python console program can't deal with Unicode characters before
                #        version 3.6.0.  For maximum compatibility, replace Unicode characters
                #        with basic ASCII equivalents.  For Python >= 3.6, could leave in place.
                #
                # Replace \u2018 (left single quote) with ASCII single quote
                if linedata.find(u'\u2018'):
                    linedata = linedata.replace(u'\u2018', "'")
                # Replace \u2019 (right single quote) with ASCII single quote
                if linedata.find(u'\u2019'):
                    linedata = linedata.replace(u'\u2019', "'")
                # Replace \u2013 (en dash) with ASCII single minus
                if linedata.find(u'\u2013'):
                    linedata = linedata.replace(u'\u2013', "-")
                # Replace \u201c (left double quote) with ASCII double quote
                if linedata.find(u'\u201c'):
                    linedata = linedata.replace(u'\u201c', '"')
                # Replace \u201d (right double quote) with ASCII double quote
                if linedata.find(u'\u201d'):
                    linedata = linedata.replace(u'\u201d', '"')

                # Transform data:
                # Note:  Parsed format is what format should be, however, there are some errors/
                #        inconsistencies with the file such as missing colons after the syslog
                #        number.
                # Parsed format:  %ASA-S-HHHLLL: MSG
                # Desired format:  ASA,S,HHH,LLL,MSG
                #
                # Remove leading '%'
                linedata = linedata[1:]
                # Split out 'ASA', Severity Number (1-7), Rest of Line
                platform, severity, linedata = linedata.split('-', 2)
                # Split out syslog number (######), Rest of Line - but check for valid format:
                # if it's not None, then it's valid
                if re.search(repat1, linedata):
                    sysnum, linedata = linedata.split(':', 1)
                # can still deal with this
                elif re.search(repat2, linedata):
                    sysnum, linedata = linedata.split(' ', 1)
                # fix entry error from vendor (1199012 should be 199012)
                elif linedata.startswith(u'1199012'):
                    sysnum, linedata = linedata.split(':', 1)
                    sysnum = u'199012'
                # fix entry errors from vendor - remove trailing % from syslog number
                elif re.search(repat3, linedata):
                    sysnum, linedata = linedata.split(':', 1)
                    sysnum = sysnum[:6]
                # Deal with wildcard numbers (n), e.g., 4000nn, which means 400000-400099
                elif re.search(repat4, linedata):
                    sysnum, linedata = linedata.split(':', 1)
                # fix entry error from vendor (73007 should be 730007)
                elif linedata.startswith(u'73007'):
                    sysnum, linedata = linedata.split(':', 1)
                    sysnum = u'730007'
                else:
                    sys.exit('Error:  Unexpected syslog format - "{}"'.format(linedata))
                # Split syslog number into group (first three digits) and number (second three
                # digits)
                syshinum = sysnum[:3]
                syslonum = sysnum[3:]
                # Note:  This still doesn't work, instead don't open csv file in Excel, but open
                #        Excel first and import the file, specify these columns as text.
                # Change format of syslog "high" and "low" numbers to prevent Excel from
                # interpreting them as text:
                #syshinum = '"=""{}"""'.format(syshinum)
                #syslonum = '"=""{}"""'.format(syslonum)
                # If there's a leading space, remove it:
                if linedata.startswith(' '):
                    sysmsg = linedata[1:]
                else:
                    sysmsg = linedata

                # Sanity check since outputting as CSV - fails, embedded commas used...
                #if sysmsg.find(',') != -1:
                #    sys.exit('Error:  Embedded comma in syslog message - "{}"'.format(sysmsg))

                # Old way, switching to using csv library
                #parsed_data = '{},{},{},{},{}'.format(platform, severity, syshinum, syslonum,
                #                                      sysmsg)

                # Format for csv library
                parsed_data = (platform, severity, syshinum, syslonum, sysmsg)

                if verbose:
                    print('Item {}, Parsed:  {}'.format(i, parsed_data))
                syslog_data.append(parsed_data)
    return syslog_data

def main(args):
    '''Retrieve syslog documentation, parse, and output to csv file'''
    # If desired:
    #headers = {'User-Agent':USERAGENT,'Accept':ACCEPT}
    url = URI+SYSLOG_DOC
    resp = getpage(url, headers=None, verbose=True)
    syslog_data = scrapedoc(resp, verbose=False)

    verbose = True
    # Create/overwrite output file
    with open(OUTFILE, 'wb') as f:
        if verbose:
            print('Exporting to CSV file "{}"...'.format(OUTFILE))
        #csvout = csv.writer(f, quoting=csv.QUOTE_ALL, dialect=csv.excel)
        csvout = csv.writer(f)
        csvout.writerow(ASAHDR)
        for line in syslog_data:
            csvout.writerow(line)

# Call main and put all logic there per best practices.
if __name__ == '__main__':
    main(sys.argv[1:])

####################################################################################################
# Post coding
#
# Only test for Python 3 compatibility:  pylint --py3k <script>.py
# pylint <script>.py
#   Score should be >= 8.0
#
# python warning options:
# * -Qwarnall - Believe check for old division usage
# * -t - issue warnings about inconsitent tab usage
# * -3 - warn about Python 3.x incompatibilities
#
# python3 warning options:
# * -b - issue warnings about mixing strings and bytes
#
# Future:
# * Testing - doctest/unittest/other
# * Logging
#

