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

# these differ from wikipedia:
_baseurl = u'http://www.conservapedia.com/'
_random_path = u'/Special:Random'
_advert = u' - Conservapedia'

class Main(Module):

    pattern = re.compile(u'^\s*(?:cp)\s+(.*?)\s*$', re.I)
    require_addressing = True
    help = u'cp <term> - look up summary of term on conservapedia'

    def __init__(self, madcow=None):
        self.wiki = Wiki(base_url=_baseurl, random_path=_random_path,
                         advert=_advert)

    def response(self, nick, args, kwargs):
        try:
            return self.wiki.get_summary(args)
        except Exception, error:
            log.warn(u'error in module %s' % self.__module__)
            log.exception(error)
            return u'%s: problem with query: %s' % (nick, error)


if __name__ == u'__main__':
    from include.utils import test_module
    test_module(Main)
