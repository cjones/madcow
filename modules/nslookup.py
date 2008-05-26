#!/usr/bin/env python

"""Perform DNS lookups"""

import re
import socket
from include.utils import Module
import logging as log

class Main(Module):
    pattern = re.compile('^\s*nslookup\s+(\S+)')
    require_addressing = True
    help = 'nslookup <ip|host> - perform DNS lookup'
    _byip = re.compile(r'^(\d+\.){3}\d+$')

    def response(self, nick, args, **kwargs):
        query = args[0]
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


if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)
