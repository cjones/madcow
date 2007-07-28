#!/usr/bin/env python

"""
Perform DNS lookups
"""

import sys
import re
import socket
import os


class MatchObject(object):

    def __init__(self, config=None, ns='madcow', dir=None):
        self.enabled = True
        self.pattern = re.compile('^\s*nslookup\s+(\S+)')
        self.requireAddressing = True
        self.thread = True
        self.wrap = True
        self.help = 'nslookup <ip|host> - perform DNS lookup'

    def response(self, **kwargs):
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


if __name__ == '__main__':
    print MatchObject().response(nick=os.environ['USER'], args=[' '.join(sys.argv[1:])])
    sys.exit(0)
