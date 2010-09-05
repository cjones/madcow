# Copyright (C) 2010 Christopher Jones
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

"""Follows wow character RSS feeds"""

from urllib import urlencode
from import feedparser
from utils import stripHTML

ARMORY_URL = 'http://www.wowarmory.com/character-feed.atom?%s'

class Main(object):

    priority = 0
    enabled = True

    def __init__(self, madcow):
        self.enabled = madcow.config.armory.enabled
        self.frequency = madcow.config.armory.updatefreq
        self.output = madcow.config.armory.channel
        self.cache = set()
        self.first_run = True
        self.characters = {('Illidan', 'Zerianna'): {},
                           ('Illidan', 'Tohst'): {},
                           ('Illidan', 'Cudicus'): {},
                           ('Illidan', 'Wept'): {},
                           ('Illidan', 'Dent'): {}}

    def response(self, *args):
        return '\n'.join(self.get_new_messages())

    def get_new_messages(self):
        for realm, character in self.characters:
            for entry in feedparser.parse(ARMORY_URL % urlencode({'r': realm, 'cn': character})).entries:
                if entry.id not in self.cache:
                    self.cache.add(entry.id)
                    if not self.first_run:
                        yield '%s: %s' % (character, stripHTML(entry.subtitle))
        self.first_run = False
