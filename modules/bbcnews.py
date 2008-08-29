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
from include import rssparser
from include.utils import Module, stripHTML
import urllib
from urlparse import urljoin
import logging as log

class Main(Module):
    pattern = re.compile('^\s*bbcnews(?:\s+(.+))?', re.I)
    require_addressing = True
    help = 'bbcnews <string> - Searches the BBC News Website'

    _error = 'Looks like the BBC aren\'t co-operating today.'
    _api_url = 'http://newsapi.bbc.co.uk/'
    _search_url = urljoin(_api_url, '/feeds/search/news/')
    _rss_url = 'http://newsrss.bbc.co.uk/'
    _world_url = urljoin(_rss_url, '/rss/newsonline_uk_edition/world/rss.xml')

    def response(self, nick, args, kwargs):
        query = args[0]

        try:
            if not query or query == 'headline':
                url = self._world_url
            else:
                url = self._search_url + urllib.quote(query)
                            
            feed = rssparser.parse(url)
            item = feed['items'][0]
            url = item['link']
            title = stripHTML(item['title'])
            sum = stripHTML(item['description'])
            return '\n'.join((url, title, sum))
            
        except Exception, e:
            log.warn('error in %s: %s' % (self.__module__, e))
            log.exception(e)
            return '%s: %s' % (nick, self._error)


if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)
