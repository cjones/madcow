#!/usr/bin/env python
#
# Copyright (C) 2007, 2008 Christopher Jones
#
# This file is part of Madcow.
#
# Madcow is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Madcow is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Madcow.  If not, see <http://www.gnu.org/licenses/>.

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

    def response(self, nick, args, kwargs):
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
