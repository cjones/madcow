#!/usr/bin/env python

"""Die roll"""

import re
import random

class MatchObject(object):
    _pattern = re.compile(r'^\s*roll\s+(-?[0-9.]+)d(-?[0-9.]+)\s*$', re.I)

    def __init__(self, *args, **kwargs):
        self.enabled = True
        self.pattern = self._pattern
        self.requireAddressing = True
        self.thread = False
        self.wrap = True
        self.help = 'roll [<numdice>d<sides>] - roll die of the specified size'
        random.seed()

    def roll(self, min, max):
        if isinstance((min * max), float):
            return random.uniform(min, max)
        else:
            return random.randint(min, max)

    def response(self, **kwargs):
        nick = kwargs['nick']
        args = kwargs['args']

        num_dice = args[0]
        if '.' in num_dice:
            num_dice = float(num_dice)
        else:
            num_dice = int(num_dice)

        sides = args[1]
        if '.' in sides:
            sides = float(sides)
        else:
            sides = int(sides)

        if sides == 0:
            return 'ZERO SIDED DIE MAKES UNIVERSE EXPLODE'
        if num_dice == 0:
            return 'ROLLING DICE 0 TIMES MEANS YOU DIE'

        min = num_dice
        max = num_dice * sides
        saving_throw = self.roll(min, max)
        save_versus = self.roll(min, max)

        if saving_throw >= save_versus:
            result = '\x033\x16\x16LIVES\x0f'
        else:
            result = '\x035\x16\x16DIES\x0f'

        return '%s rolls %s, needs %s, %s %s' % (nick, saving_throw,
                save_versus, nick, result)

if __name__ == '__main__':
    import sys
    print MatchObject().response(nick='user', args=sys.argv[1:])
