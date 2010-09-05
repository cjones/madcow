"""Die roll"""

import re
import random
import math
from madcow.util import Module
from madcow.util.color import ColorLib

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
