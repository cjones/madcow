#!/usr/bin/env python

"""Grab the latest blog post from an RSS feed"""

""" Copyright 2013 ActiveState Software Inc. """

import re
import feedparser
from madcow.util import Module
from madcow.conf import settings
import urllib
from urlparse import urljoin

class Main(Module):

    pattern = re.compile(u'^\s*blog\s*$', re.I)
    require_addressing = False
    _rss_url = settings.BLOG_RSS_URL
    help = u'blog - get the latest blog post from %s' % (_rss_url)
    error = u'Looks like the blog isn\'t co-operating today.'

    def response(self, nick, args, kwargs):
        entries = feedparser.parse(self._rss_url).entries
        if entries:
            item = entries[0]
            return u'\n'.join([item.title, item.link, item.updated])
        else:
            return u'%s' % (self.error)
