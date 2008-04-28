#!/usr/bin/env python

"""Perform DNS lookups"""

import sys
import re
import socket
import os
from include.utils import Base

class Main(Base):
    enabled = True
    pattern = re.compile('^\s*nslookup\s+(\S+)')
    require_addressing = True


    help = 'nslookup <ip|host> - perform DNS lookup'

    _byip = re.compile(r'^(\d+\.){3}\d+$')

    def response(self, **kwargs):
        nick = kwargs['nick']
        query = kwargs['args'][0]

        if self._byip.search(query):
            try:
                response = socket.gethostbyaddr(query)[0]
            except:
                response = 'No hostname for that IP'
        else:
            try:
                response = socket.gethostbyname(query)
            except:
                response = 'No IP for that hostname'

        return '%s: %s' % (nick, response)


def main():
    try:
        main = Main()
        args = main.pattern.search(' '.join(sys.argv[1:])).groups()
        print main.response(nick=os.environ['USER'], args=args)
    except Exception, e:
        print 'no match: %s' % e

if __name__ == '__main__':
    sys.exit(main())
