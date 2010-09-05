#!/usr/bin/env python
#
# Copyright (C) 2007-2008 Christopher Jones
#
# This file is part of Madcow.
#
# Madcow is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# Madcow is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License
# along with Madcow.  If not, see <http://www.gnu.org/licenses/>.

"""Use Google to get time's in various places"""

from madcow.util import Module
from google import Google

import re

__version__ = '0.1'
__author__ = 'Chris Jones <cjones@gruntle.org>'
__all__ = []

class WorldClock(Module):

    pattern = re.compile(r'^\s*(?:clock|time)(?:\s*[:-]\s*|\s+)(.+?)\s*$', re.I)
    help = u'time <location> - ask google what time it is somewhere'
    in_re = re.compile(r'^\s*in\s+', re.I)

    def __init__(self, madcow=None):
        self.madcow = madcow
        self.google = Google()

    def response(self, nick, args, kwargs):
        try:
            query = args[0]
            query = self.in_re.sub('', query)
            result = self.google.clock(query)
            if result:
                return u'%s: %s' % (nick, result)
            else:
                return u"%s: They don't do the whole time thing in \"%s\"" % (
                        nick, query)
        except Exception, error:
            self.log.warn('error in module %s' % self.__module__)
            self.log.exception(error)
            return u'%s: %s' % (nick, error)


Main = WorldClock


if __name__ == u'__main__':
    from madcow.util import test_module
    test_module(Main)
