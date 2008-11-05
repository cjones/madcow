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

__version__ = '0.1'
__author__ = 'Chris Jones <cjones@gruntle.org>'

class Main(Module):

    pattern = re.compile(r'^\s*obama\s*$', re.I)
    oday = 1232470800  # jan 20, 2009 @ 9pm
    units = [('second', 60), ('minute', 60), ('hour', 24), ('day', 0)]

    def response(self, nick, args, kwargs):
        try:
            return '%s: President Obama in: %s' % (
                    nick, self.human_readable(self.oday - time.time()))
        except Exception, error:
            log.warn('error in module %s' % self.__module__)
            log.exception(error)
            return '%s: %s' % (nick, error)

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
                    name += 's'
                units.append('%s %s' % (r, name))
            if not n:
                break
        if units:
            units.reverse()
            return ' '.join(units)


if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)
