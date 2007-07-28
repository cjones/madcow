#!/usr/bin/env python

"""
Generate random figlet of the ultimate insult!
"""

import sys
import re
from include.pyfiglet import Figlet
import random
import os


class MatchObject(object):

    def __init__(self, config=None, ns='madcow', dir='..'):
        self.enabled = True
        self.pattern = re.compile('^\s*yourmom\s*$')
        self.requireAddressing = True
        self.thread = False
        self.wrap = False
        self.help = 'yourmom - random figlet of the ultimate insult'

        zipfile = '%s/include/fonts.zip' % dir
        self.figlet = Figlet(zipfile=zipfile)

        # pre-approved list of fonts to use
        self.fonts = (
            '5lineoblique', 'acrobatic', 'alligator', 'alligator2', 'asc_____',
            'ascii___', 'avatar', 'big', 'bigchief', 'block', 'bubble', 'bulbhead',
            'chunky', 'colossal', 'computer', 'cosmic', 'crawford', 'cursive',
            'digital', 'dotmatrix', 'double', 'drpepper', 'eftifont',
            'eftirobot', 'eftiwall', 'eftiwater', 'epic', 'fourtops', 'fuzzy',
            'goofy', 'graceful', 'gradient', 'graffiti', 'hollywood', 'invita',
            'italic', 'larry3d', 'lean', 'maxfour', 'mini', 'nvscript', 'o8',
            'pawp', 'pepper', 'puffy', 'rectangles', 'shadow', 'slant', 'small',
            'smkeyboard', 'smshadow', 'smslant', 'speed', 'stampatello',
            'standard', 'straight', 'twopoint'
        )

    def response(self, **kwargs):
        try:
            self.figlet.setFont(font=random.choice(self.fonts))
            text = self.figlet.renderText('your mom')
            return text

        except Exception, e:
            print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
            return '%s: your mom :(' % nick


if __name__ == '__main__':
    print MatchObject().response(nick=os.environ['USER'])
    sys.exit(0)
