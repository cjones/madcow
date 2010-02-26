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
from include import feedparser
from include.utils import stripHTML
from time import mktime, time, timezone
import re

ARMORY_URL = 'http://www.wowarmory.com/character-feed.atom?%s'

class Main(object):

    priority = 0

    def __init__(self, madcow):
        self.enabled = madcow.config.armory.enabled
        self.frequency = madcow.config.armory.updatefreq
        self.output = madcow.config.armory.channel
        self.feed = ArmoryFeed()

    def response(self, *args):
        """This is called by madcow, should return a string or None"""
        return '\n'.join(self.feed.get_new_messages())


class ArmoryFeed(object):

    """Checks armory"""

    def __init__(self):
        # XXX move this into .. something else
        self.characters = {('Illidan', 'Zerianna'): {},
                           ('Illidan', 'Tohst'): {},
                           ('Illidan', 'Cudicus'): {},
                           ('Illidan', 'Wept'): {},
                           ('Illidan', 'Dent'): {}}
        self.last_check = time()

    def get_new_messages(self):
        now = time()
        for realm, character in self.characters:
            for published, message in self.get_character_feed(realm, character):
                if published > self.last_check:
                    yield '%s: %s' % (character, message)
        self.last_check = now

    def get_character_feed(self, realm, character):
        for entry in feedparser.parse(ARMORY_URL % urlencode({'r': realm, 'cn': character})).entries:
            yield mktime(entry.published_parsed) - timezone, stripHTML(entry.subtitle)
