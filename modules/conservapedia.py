#!/usr/bin/env python
#
# Copyright (C) 2007, 2008 Christopher Jones
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

"""Plugin to return summary from ConservaPedia (lol)"""

from include.wiki import Wiki
from include.utils import Module
import re
import logging as log

class ConservaPedia(Wiki):

    base_url = u'http://www.conservapedia.com/'
    random_path = u'/Special:Random'
    search_path = u'/Special:Search'
    advert = u' - Conservapedia'


class ChristoPedia(Wiki):

    base_url = u'http://christopedia.us/'
    advert = u' - Christopedia, the Christian encyclopedia'


class Main(Module):

    pattern = re.compile(u'^\s*(c[ph])\s+(.+?)\s*$', re.I)
    help = u'[cp|ch] <term> - look up offensive and inaccurate info'

    def __init__(self, madcow=None):
        self.wikis = dict(cp=ConservaPedia(), ch=ChristoPedia())

    def response(self, nick, args, kwargs):
        try:
            return self.wikis[args[0].lower()].get_summary(args[1])
        except Exception, error:
            log.warn(u'error in module %s' % self.__module__)
            log.exception(error)
            return u'%s: problem with query: %s' % (nick, error)


if __name__ == u'__main__':
    from include.utils import test_module
    test_module(Main)
