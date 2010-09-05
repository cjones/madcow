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

"""High Precision Care-O-Meter"""

from madcow.util import Module

import re
from google import Google

__version__ = u'0.1'
__author__ = u'cj_ <cjones@gruntle.org>'
__all__ = []

class Main(Module):

    pattern = None
    pattern = re.compile(r'^\s*care(?:(?:[- ]?o)?[- ]?meter)?\s+(.+)\s*$', re.I)
    help = u'care <#> - display a care-o-meter'
    error = u'invalid care factor'
    isnum = re.compile(r'^\s*[0-9.]+\s*$')
    sep = re.compile(r'\s*=\s*')
    numsep = re.compile(r'(\d)\s+(\d)')
    title = u'CARE-O-METER'

    # settings
    size = 40
    min = 0
    max = 100

    def __init__(self, madcow=None):
        self.google = Google()
        self.bar = [i for i in u'.' * self.size]
        self.size = float(self.size)
        self.min = float(self.min)
        self.max = float(self.max)
        self.range = self.max - self.min

    def response(self, nick, args, kwargs):
        try:
            val = args[0]
            if not self.isnum.search(val):
                # try google calculator if not a number
                val = self.google.calculator(val)
                val = self.numsep.sub(r'\1\2', val)
                val = self.sep.split(val)[1]
                val = val.split()[0]
            val = float(val)

            # sanity check value
            if val < self.min:
                val = self.min
            elif val > self.max:
                val = self.max

            # create bar
            pos = int(round((self.size - 1) * ((val - self.min) / self.range)))
            bar = list(self.bar)
            bar[pos] = u'o'
            bar = u''.join(bar)
            bar = u'|' + bar + u'|'
            return u'%s: %s' % (self.title, bar)

        except Exception, error:
            self.log.warn(u'error in module %s' % self.__module__)
            self.log.exception(error)
            return u'%s: %s' % (nick, self.error)


if __name__ == u'__main__':
    from madcow.util import test_module
    test_module(Main)
