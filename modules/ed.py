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

"""Plugin to return summary from ED"""

from include.utils import Module
from include.wiki import Wiki
import re
import logging as log

class Dramatica(Wiki):

    base_url = u'http://encyclopediadramatica.com/'
    random_path = u'/Special:Random'
    search_path = u'/Special:Search'
    advert = u' - Encyclopedia Dramatica'


class Main(Module):

    pattern = re.compile(u'^\s*(?:ed|drama)\s+(.*?)\s*$', re.I)
    require_addressing = True
    help = u'ed <term> - look up summary of term on dramatica'

    def __init__(self, *args, **kwargs):
        self.wiki = Dramatica()

    def response(self, nick, args, kwargs):
        try:
            return unicode(self.wiki.get_summary(args))
        except Exception, error:
            log.warn(u'error in module %s' % self.__module__)
            log.exception(error)
            return u'%s: problem with query: %s' % (nick, error)


if __name__ == u'__main__':
    from include.utils import test_module
    test_module(Main)
