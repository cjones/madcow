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

"""Countdown to Obamanation"""

from include.utils import Module
import logging as log
import re
import time

__version__ = u'0.1'
__author__ = u'Chris Jones <cjones@gruntle.org>'

class Main(Module):

    pattern = re.compile(r'^\s*obama\s*$', re.I)
    oday = 1232470800  # jan 20, 2009 @ 9pm
    units = [(u'second', 60),
             (u'minute', 60),
             (u'hour', 24),
             (u'day', 7),
             (u'week', 4),
             (u'month', 0)]

    def response(self, nick, args, kwargs):
        try:
            e = self.oday - time.time()
            if e <= 0:
                return u'WE HAVE REACHED O-DAY!'
            ms = int((e - int(e)) * 1000)
            return u'%s: President Obama in: %s %d milliseconds' % (
                    nick, self.human_readable(e), ms)
        except Exception, error:
            log.warn(u'error in module %s' % self.__module__)
            log.exception(error)
            return u'%s: %s' % (nick, error)

    @classmethod
    def human_readable(cls, n):
        units = []
        for name, size in cls.units:
            n = int(n)
            if size and n >= size:
                r = n % size
                n = n / size
            else:
                r = n
                n = 0
            if r:
                if r > 1:
                    name += u's'
                units.append(u'%s %s' % (r, name))
            if not n:
                break
        if units:
            units.reverse()
            return u' '.join(units)


if __name__ == u'__main__':
    from include.utils import test_module
    test_module(Main)
