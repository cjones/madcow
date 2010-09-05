#!/usr/bin/env python
#
# Copyright (C) 2010 Christopher Jones
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

"""Get sunrise or sunset from google"""

import logging as log
import re

from madcow.util import Module, stripHTML
from madcow.util.http import getsoup
from madcow.util.color import ColorLib
from learn import Main as Learn
from google import Google

__version__ = '1.0'
__author__ = 'Chris Jones <cjones@gruntle.org>'
__all__ = []

class Main(Module):

    pattern = re.compile(r'^\s*(sunrise|sunset)(?:\s+(@?)(.+?))?\s*$', re.I)
    help = '(sunrise|sunset) [location|@nick] - get time of sun rise/set'

    def __init__(self, madcow=None):
        if madcow is not None:
            self.colorlib = madcow.colorlib
        else:
            self.colorlib = ColorLib('ansi')
        try:
            self.learn = Learn(madcow=madcow)
        except:
            self.learn = None
        self.google = Google()
        super(Main, self).__init__(madcow)

    def response(self, nick, args, kwargs):
        query, args = args[0], args[1:]
        try:
            if not args[1]:
                args = 1, nick
            if args[0]:
                location = self.learn.lookup('location', args[1])
                if not location:
                    return u'%s: Try: set location <nick> <location>' % nick
            else:
                location = args[1]
            response = self.google.sunrise_sunset(query, location)
        except Exception, error:
            log.warn('error in module %s' % self.__module__)
            log.exception(error)
            response = u"That place doesn't have a sun, sorry."
        return u'%s: %s' % (nick, response)

if __name__ == '__main__':
    from madcow.util import test_module
    test_module(Main)
