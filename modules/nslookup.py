#!/usr/bin/env python

# Perform DNS lookups

import sys
import re
import socket

# class for this module
class MatchObject(object):
    def __init__(self, config=None, ns='default', dir=None):
        self.enabled = True                # True/False - enabled?
        self.pattern = re.compile('^\s*nslookup\s+(\S+)')    # regular expression that needs to be matched
        self.requireAddressing = True            # True/False - require addressing?
        self.thread = True                # True/False - should bot spawn thread?
        self.wrap = True                # True/False - wrap output?
        self.help = 'nslookup <ip|host> - perform DNS lookup'

    # function to generate a response
    def response(self, *args, **kwargs):
        nick = kwargs['nick']
        args = kwargs['args']
        query = args[0]
        if re.search('^(\d+\.){3}\d+$', query):
            try: response = socket.gethostbyaddr(query)[0]
            except: response = 'No hostname for that IP'
        else:
            try: response = socket.gethostbyname(query)
            except: response = 'No IP for that hostname'

        return '%s: %s' % (nick, response)


# this is just here so we can test the module from the commandline
def main(argv = None):
    if argv is None: argv = sys.argv[1:]
    obj = MatchObject()
    print obj.response(nick='testUser', args=argv)

    return 0

if __name__ == '__main__': sys.exit(main())
