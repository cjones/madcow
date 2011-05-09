#!/usr/bin/env python

"""Scrape BBC news"""

import re
import feedparser
from madcow.util import Module
import urllib
from urlparse import urljoin

class Main(Module):

    pattern = re.compile(u'^\s*bbc(?:news)?\s*$', re.I)
    require_addressing = True
    help = u'bbcnews - get BBC headline news'
    error = u'Looks like the BBC aren\'t co-operating today.'

    _rss_url = u'http://newsrss.bbc.co.uk/'
    _world_url = urljoin(_rss_url, u'/rss/newsonline_uk_edition/world/rss.xml')

    def response(self, nick, args, kwargs):
        item = feedparser.parse(self._world_url).entries[0]
        return u' | '.join([item.link, item.description, item.updated])
