#!/usr/bin/env python

"""CNN Headline"""

import re
import feedparser
from madcow.util import strip_html, Module

class Main(Module):

    pattern = re.compile(r'^\s*cnn\s*$', re.I)
    help = 'cnn - cnn headline'
    url = 'http://rss.cnn.com/rss/cnn_topstories.rss'

    def response(self, nick, args, kwargs):
        item = feedparser.parse(self.url).entries[0]
        body = strip_html(item.description).strip()
        return u' | '.join([item.link, body, item.updated])
