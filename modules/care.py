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

from include.utils import Module
import logging as log
import re
from include.google import Google

__version__ = '0.1'
__author__ = 'cj_ <cjones@gruntle.org>'
__all__ = []

class Main(Module):
    pattern = None
    pattern = re.compile(r'^\s*care(?:(?:[- ]?o)?[- ]?meter)?\s+(.+)\s*$', re.I)
    help = 'care <#> - display a care-o-meter'
    error = 'invalid care factor'
    isnum = re.compile(r'^\s*[0-9.]+\s*$')
    sep = re.compile(r'\s*=\s*')
    numsep = re.compile(r'(\d)\s+(\d)')
    title = 'CARE-O-METER'

    # settings
    size = 40
    min = 0
    max = 100

    def __init__(self, madcow=None):
        self.google = Google()
        self.bar = [i for i in '.' * self.size]
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
            bar[pos] = 'o'
            bar = ''.join(bar)
            bar = '|' + bar + '|'
            response = '%s: %s' % (self.title, bar)
            return response
                
        except Exception, e:
            log.warn('error in %s: %s' % (self.__module__, e))
            log.exception(e)
            return '%s: %s' % (nick, self.error)


if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)
