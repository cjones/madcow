"""Perform DNS lookups"""

import re
import socket
from madcow.util import Module

class Main(Module):

    pattern = re.compile(u'^\s*nslookup\s+(\S+)')
    require_addressing = True
    help = u'nslookup <ip|host> - perform DNS lookup'
    _byip = re.compile(r'^(\d+\.){3}\d+$')

    def response(self, nick, args, kwargs):
        query = args[0]
        if self._byip.search(query):
            try:
                response = socket.gethostbyaddr(query)[0]
            except:
                response = u'No hostname for that IP'
        else:
            try:
                response = socket.gethostbyname(query)
            except:
                response = u'No IP for that hostname'
        return u'%s: %s' % (nick, response)
