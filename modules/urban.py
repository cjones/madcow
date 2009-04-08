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

"""Look up a definition in the Urban Dictionary"""

import re
from include import SOAPpy
from include.utils import Module, stripHTML
import logging as log

class Main(Module):

    pattern = re.compile(u'^\s*urban\s+(.+)')
    require_addressing = True
    help = u'urban <phrase> - look up a word/phrase on urban dictionary'
    key = u'a979884b386f8b7ea781754892f08d12'
    error = u"%s: So obscure even urban dictionary doesn't know what it means"

    def __init__(self, madcow=None):
        self.server = SOAPpy.SOAPProxy(u"http://api.urbandictionary.com/soap")

    def response(self, nick, args, kwargs):
        try:
            words = args[0].split()
            if words[-1].isdigit():
                i = int(words[-1])
                term = u' '.join(words[:-1])
            else:
                i = 1
                term = u' '.join(words)
            items = self.server.lookup(self.key, term)
            max = len(items)
            if max == 0:
                return self.error % nick

            if i > max:
                return u'%s: CRITICAL BUFFER OVERFLOW ERROR' % nick

            item = items[i - 1]
            response = u'%s: [%s/%s] %s - Example: %s' % (
                    nick, i, max, item.definition, item.example)
            return stripHTML(response)

        except Exception, error:
            log.warn(u'error in module %s' % self.__module__)
            log.exception(error)
            return u"%s: Serious problems: %s" % (nick, error)


if __name__ == u'__main__':
    from include.utils import test_module
    test_module(Main)
