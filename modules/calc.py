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

"""Use Google as a calculator"""

import re
from include.utils import Module
from include.google import Google
import logging as log

class Main(Module):
    pattern = re.compile('^\s*calc\s+(.+)', re.I)
    require_addressing = True
    help = 'calc <expression> - pass expression to google calculator'

    def __init__(self, madcow=None):
        self.google = Google()

    def response(self, nick, args, kwargs):
        try:
            query = args[0]
            response = self.google.calculator(query)
            return '%s: %s' % (nick, response)
        except Exception, e:
            log.warn('error in %s: %s' % (self.__module__, e))
            log.exception(e)
            return '%s: No results (bad syntax?)' % nick


if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)
