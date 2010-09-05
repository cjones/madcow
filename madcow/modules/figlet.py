#!/usr/bin/env python
#
# Copyright (C) 2007, 2008 Christopher Jones and James Johnston
#
# This file is part of Madcow.
#
# Madcow is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Madcow is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Madcow.  If not, see <http://www.gnu.org/licenses/>.

"""Generate ASCII text using figlet! """

import re
from pyfiglet import Figlet
from utils import Module
import random
import os
import logging as log
from import encoding

__author__ = u'James Johnston <jjohnston@email4life.com>'

class Main(Module):

    pattern = re.compile(u'^\s*figlet\s+(.+?)\s*$')
    require_addressing = True
    allow_threading = False
    help = u'figlet <text> - ASCII text generator'

    def __init__(self, madcow=None):
        zipfile = os.path.join(madcow.prefix, u'include/fonts.zip')
        self.figlet = Figlet(zipfile=zipfile)

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

    def response(self, nick, args, kwargs):
        try:
            self.figlet.setFont(font=random.choice(self.fonts))
            text = self.figlet.renderText(args[0])
            return encoding.convert(text)

        except Exception, error:
            log.warn(u'error in module %s' % self.__module__)
            log.exception(error)
            return u'%s: figlet :(' % nick


if __name__ == u'__main__':
    from utils import test_module
    test_module(Main)
