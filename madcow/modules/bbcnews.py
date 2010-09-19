#!/usr/bin/env python

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
    error = u'Looks like the BBC aren\'t co-operating today.'

    _api_url = u'http://newsapi.bbc.co.uk/'
    _search_url = urljoin(_api_url, u'/feeds/search/news/')
    _rss_url = u'http://newsrss.bbc.co.uk/'
    _world_url = urljoin(_rss_url, u'/rss/newsonline_uk_edition/world/rss.xml')

    def response(self, nick, args, kwargs):
        query = args[0]
        if not query or query == u'headline':
            url = self._world_url
        else:
            url = self._search_url + urllib.quote(query.encode('utf-8'))
        item = feedparser.parse(url).entries[0]
        return u' | '.join([item.link, item.description, item.updated])
