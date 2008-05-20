#!/usr/bin/env python

"""Generate random figlet of the ultimate insult! """

import sys
import re
from include.pyfiglet import Figlet
from include.utils import Module
import random
import os

class Main(Module):
    pattern = re.compile('^\s*yourmom\s*$')
    require_addressing = True
    help = 'yourmom - random figlet of the ultimate insult'

    def __init__(self, madcow=None):
        zipfile = os.path.join(madcow.dir, 'include/fonts.zip')
        self.figlet = Figlet(zipfile=zipfile)

        # pre-approved list of fonts to use
        self.fonts = (
            '5lineoblique', 'acrobatic', 'alligator', 'alligator2', 'asc_____',
            'ascii___', 'avatar', 'big', 'bigchief', 'block', 'bubble',
            'bulbhead', 'chunky', 'colossal', 'computer', 'cosmic',
            'crawford', 'cursive', 'digital', 'dotmatrix', 'double',
            'drpepper', 'eftifont', 'eftirobot', 'eftiwall', 'eftiwater',
            'epic', 'fourtops', 'fuzzy', 'goofy', 'graceful', 'gradient',
            'graffiti', 'hollywood', 'invita', 'italic', 'larry3d', 'lean',
            'maxfour', 'mini', 'nvscript', 'o8', 'pawp', 'pepper', 'puffy',
            'rectangles', 'shadow', 'slant', 'small', 'smkeyboard',
            'smshadow', 'smslant', 'speed', 'stampatello', 'standard',
            'straight', 'twopoint'
        )

    def response(self, nick, args, **kwargs):
        try:
            self.figlet.setFont(font=random.choice(self.fonts))
            text = self.figlet.renderText('your mom')
            return text

        except Exception, e:
            print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
            return '%s: your mom :(' % nick


