#!/usr/bin/env python
#
# Copyright (C) 2007, 2008 Christopher Jones and Matt Brown
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

"""Scrape BBC news"""

import re
import feedparser
from madcow.util import Module
import urllib
from urlparse import urljoin


class Main(Module):

    pattern = re.compile(u'^\s*bbc(?:news)?(?:\s+(.+))?', re.I)
    require_addressing = True
    help = u'bbcnews <string> - Searches the BBC News Website'
    _error = u'Looks like the BBC aren\'t co-operating today.'
    _api_url = u'http://newsapi.bbc.co.uk/'
    _search_url = urljoin(_api_url, u'/feeds/search/news/')
    _rss_url = u'http://newsrss.bbc.co.uk/'
    _world_url = urljoin(_rss_url, u'/rss/newsonline_uk_edition/world/rss.xml')

    def response(self, nick, args, kwargs):
        query = args[0]
        try:
            if not query or query == u'headline':
                url = self._world_url
            else:
                url = self._search_url + urllib.quote(query.encode('utf-8'))
            item = feedparser.parse(url).entries[0]
            return u' | '.join([item.link, item.description, item.updated])

        except Exception, error:
            self.log.warn(u'error in module %s' % self.__module__)
            self.log.exception(error)
            return u'%s: %s' % (nick, self._error)


if __name__ == u'__main__':
    from madcow.util import test_module
    test_module(Main)
