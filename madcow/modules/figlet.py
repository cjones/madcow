"""Generate ASCII text using figlet! """

import re
from pyfiglet import Figlet
from madcow.util import Module
import random
import os
import encoding

__author__ = u'James Johnston <jjohnston@email4life.com>'

class Main(Module):

    pattern = re.compile(u'^\s*figlet\s+(.+?)\s*$')
    require_addressing = True
    allow_threading = False
    help = u'figlet <text> - ASCII text generator'

    # pre-approved list of fonts to use
    self.fonts = (
        u'5lineoblique', u'acrobatic', u'alligator', u'alligator2', u'asc_____',
        u'ascii___', u'avatar', u'big', u'bigchief', u'block', u'bubble',
        u'bulbhead', u'chunky', u'colossal', u'computer', u'cosmic',
        u'crawford', u'cursive', u'digital', u'dotmatrix', u'double',
        u'drpepper', u'eftifont', u'eftirobot', u'eftiwall', u'eftiwater',
        u'epic', u'fourtops', u'fuzzy', u'goofy', u'graceful', u'gradient',
        u'graffiti', u'hollywood', u'invita', u'italic', u'larry3d', u'lean',
        u'maxfour', u'mini', u'nvscript', u'o8', u'pawp', u'pepper', u'puffy',
        u'rectangles', u'shadow', u'slant', u'small', u'smkeyboard',
        u'smshadow', u'smslant', u'speed', u'stampatello', u'standard',
        u'straight', u'twopoint'
    )

    def init(self):
        zipfile = os.path.join(madcow.base, u'include/fonts.zip')
        self.figlet = Figlet(zipfile=zipfile)

    def response(self, nick, args, kwargs):
        self.figlet.setFont(font=random.choice(self.fonts))
        text = self.figlet.renderText(args[0])
        return encoding.convert(text)
