#!/usr/bin/env python

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
