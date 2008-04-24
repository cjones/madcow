#!/usr/bin/env python

"""Die roll"""

import re
import random
import math

class MatchObject(object):
    _allow = '-?(?:[0-9.]+j?|pi|e)'
    _regex = '^\s*roll\s+(%s)d(%s)\s*$' % (_allow, _allow)

    def __init__(self, *args, **kwargs):
        self.enabled = True
        self.pattern = re.compile(self._regex, re.I)
        self.requireAddressing = True
        self.thread = False
        self.wrap = True
        self.help = 'roll [<numdice>d<sides>] - roll die of the specified size'
        random.seed()

    def roll(self, min, max):
        if isinstance((min * max), (float, complex)):
            return random.uniform(min, max)
        else:
            return random.randint(min, max)

    def response(self, **kwargs):
        nick = kwargs['nick']
        args = kwargs['args']

        num_dice = args[0].lower()
        if num_dice == 'pi':
            num_dice = math.pi
        elif num_dice == 'e':
            num_dice = math.e
        elif num_dice.endswith('j'):
            num_dice = complex(num_dice)
        elif '.' in num_dice:
            num_dice = float(num_dice)
        else:
            num_dice = int(num_dice)

        sides = args[1].lower()
        if sides == 'pi':
            sides = math.pi
        elif sides == 'e':
            sides = math.e
        elif sides.endswith('j'):
            sides = complex(sides)
        elif '.' in sides:
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

        try:
            if saving_throw >= save_versus:
                result = '\x033\x16\x16LIVES\x0f'
            else:
                result = '\x035\x16\x16DIES\x0f'
        except:
            result = '\x037\x16\x16IS IN LIMBO\x0f'

        return '%s rolls %s, needs %s, %s %s' % (nick, saving_throw,
                save_versus, nick, result)

if __name__ == '__main__':
    import sys
    print MatchObject().response(nick='user', args=sys.argv[1:])
