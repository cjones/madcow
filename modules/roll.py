#!/usr/bin/env python

"""Die roll"""

import re
import random
import math
from include.utils import Module
import os
import logging as log

class Main(Module):
    _allow = '-?(?:[0-9.]+j?|pi|e)'
    _regex = '^\s*roll\s+(%s?)d(%s)\s*$' % (_allow, _allow)
    pattern = re.compile(_regex, re.I)
    allow_threading = False
    require_addressing = True
    help = 'roll [<numdice>d<sides>] - roll die of the specified size'
    _color_map = {'red': 5, 'yellow': 7, 'green': 3}

    def roll(self, min, max):
        if isinstance((min * max), (float, complex)):
            return random.uniform(min, max)
        else:
            return random.randint(min, max)

    def normalize(self, val):
        try:
            val = val.lower()
            if val == 'pi':
                val = math.pi
            elif val == 'e':
                val = math.e
            elif val.endswith('j'):
                val = complex(val)
            elif '.' in val:
                val = float(val)
            else:
                val = int(val)
        except:
            val = 1
        return val

    def colorize(self, text, color):
        color_code = self._color_map[color]
        return '\x03%d\x16\x16%s\x0f' % (color_code, text)

    def response(self, nick, args, kwargs):
        num_dice = self.normalize(args[0])
        sides = self.normalize(args[1])

        if sides == 0 or num_dice == 0:
            return 'GOOD JOB, UNIVERSE %s' % self.colorize('EXPLODES', 'red')

        if sides == 1 and num_dice == 1:
            return 'CHEATING DETECTED, YOU %s' % self.colorize('DIE', 'red')

        min = num_dice
        max = num_dice * sides
        saving_throw = self.roll(min, max)
        save_versus = self.roll(min, max)

        try:
            if saving_throw >= save_versus:
                result = self.colorize('LIVES', 'green')
            else:
                result = self.colorize('DIES', 'red')
        except:
            result = self.colorize('IS TOO COMPLEX', 'yellow')

        return '%s rolls %s, needs %s, %s %s' % (nick, saving_throw,
                save_versus, nick, result)


if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)
