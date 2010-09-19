"""Generate ASCII text using figlet! """

import re
import pyfiglet
from madcow.util import Module, encoding
import random
import os

__author__ = u'James Johnston <jjohnston@email4life.com>'

class Main(Module):

    pattern = re.compile(u'^\s*figlet\s+(.+?)\s*$')
    require_addressing = True
    allow_threading = False
    help = u'figlet <text> - ASCII text generator'

    # pre-approved list of fonts to use
    fonts = (
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
        self.zipfile = os.path.join(os.path.dirname(pyfiglet.__file__), 'fonts.zip')

    def response(self, nick, args, kwargs):
        figlet = pyfiglet.Figlet(zipfile=self.zipfile)
        figlet.set_font(font_name=random.choice(self.fonts))
        return encoding.convert(figlet.render_text(args[0]))
