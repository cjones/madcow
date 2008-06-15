#!/usr/bin/env python

"""Generate ASCII text using figlet! """

import re
from include.pyfiglet import Figlet
from include.utils import Module
import random
import os
import logging as log

__author__ = 'James Johnston <jjohnston@email4life.com>'

class Main(Module):
    pattern = re.compile('^\s*figlet\s+(.+?)\s*$')
    require_addressing = True
    allow_threading = False
    help = 'figlet <text> - ASCII text generator'

    def __init__(self, madcow=None):
        zipfile = os.path.join(madcow.prefix, 'include/fonts.zip')
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

    def response(self, nick, args, kwargs):
        try:
            self.figlet.setFont(font=random.choice(self.fonts))
            text = self.figlet.renderText(args[0])
            return text

        except Exception, e:
            log.warn('error in %s: %s' % (self.__module__, e))
            log.exception(e)
            return '%s: figlet :(' % nick


if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)
