#!/usr/bin/env python
#
# Copyright (C) 2007, 2008 Christopher Jones and Todd Dailey
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

"""Die roll"""

import re
import random
import math
from include.utils import Module
from include.colorlib import ColorLib
import os
import logging as log

class Main(Module):

    _allow = u'-?(?:[0-9.]+j?|pi|e)'
    _regex = u'^\s*roll\s+(%s?)d(%s)\s*$' % (_allow, _allow)
    pattern = re.compile(_regex, re.I)
    allow_threading = False
    require_addressing = True
    help = u'roll [<numdice>d<sides>] - roll die of the specified size'

    def __init__(self, madcow=None):
        if madcow is not None:
            self.colorlib = madcow.colorlib
        else:
            self.colorlib = ColorLib(u'ansi')

    def roll(self, min, max):
        if isinstance((min * max), (float, complex)):
            return random.uniform(min, max)
        else:
            return random.randint(min, max)

    def normalize(self, val):
        try:
            val = val.lower()
            if val == u'pi':
                val = math.pi
            elif val == u'e':
                val = math.e
            elif val.endswith(u'j'):
                val = complex(val)
            elif u'.' in val:
                val = float(val)
            else:
                val = int(val)
        except:
            val = 1
        return val

    def colorize(self, text, color):
        return self.colorlib.get_color(color, text=text)

    def response(self, nick, args, kwargs):
        num_dice = self.normalize(args[0])
        sides = self.normalize(args[1])

        if sides == 0 or num_dice == 0:
            return u'GOOD JOB, UNIVERSE %s' % self.colorize(u'EXPLODES', u'red')

        if sides == 1 and num_dice == 1:
            return u'CHEATING DETECTED, YOU %s' % self.colorize(u'DIE', u'red')

        min = num_dice
        max = num_dice * sides
        saving_throw = self.roll(min, max)
        save_versus = self.roll(min, max)

        try:
            if saving_throw >= save_versus:
                result = self.colorize(u'LIVES', u'green')
            else:
                result = self.colorize(u'DIES', u'red')
        except:
            result = self.colorize(u'IS TOO COMPLEX', u'yellow')

        return u'%s rolls %s, needs %s, %s %s' % (nick, saving_throw,
                save_versus, nick, result)


if __name__ == u'__main__':
    from include.utils import test_module
    test_module(Main)
