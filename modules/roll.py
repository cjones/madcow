"""Die roll"""

import re
import random

class MatchObject(object):
    _sides = 20

    def __init__(self, *args, **kwargs):
        self.enabled = True
        self.pattern = re.compile(r'^\s*roll\s+d(\d{0,3})\s*$', re.I)
        self.requireAddressing = True
        self.thread = False
        self.wrap = True
        self.help = 'roll [d<number>] - roll die of the specified size'

    def roll(self, sides):
        return random.randint(1, sides)

    def response(self, **kwargs):
        nick = kwargs['nick']
        args = kwargs['args']
        try:
            sides = int(args[0])
        except:
            sides = self._sides
        if not sides:
            sides = self._sides
        saving_throw, save_versus = self.roll(sides), self.roll(sides)
        if saving_throw >= save_versus:
            result = 'LIVES'
        else:
            result = 'DIES'
        return '%s rolls %s, needs %s, %s %s' % (nick, saving_throw,
                save_versus, nick, result)

