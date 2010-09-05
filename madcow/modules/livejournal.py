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

"""Read from LiveJournal"""

import re
from import feedparser
from utils import Module, stripHTML
from useragent import geturl
from urlparse import urljoin
import logging as log

class Main(Module):

    enabled = True
    pattern = re.compile(u'^\s*(?:livejournal|lj)(?:\s+(\S+))?')
    require_addressing = True
    help = u'lj [user] - get latest entry to an lj, omit user for a random one'
    baseURL = u'http://livejournal.com'
    randomURL = urljoin(baseURL, u'/random.bml')
    max = 800

    def response(self, nick, args, kwargs):
        try:
            try:
                user = args[0]
            except:
                user = None
            if user is None or user == u'':
                doc = geturl(self.randomURL)
                user = re.search(u'"currentJournal": "(.*?)"', doc).group(1)
            url = urljoin(self.baseURL, u'/users/%s/data/rss' % user)
            rss = feedparser.parse(url)
            entry = stripHTML(rss.entries[0].description)[:self.max]
            page = stripHTML(rss.channel.link)
            return u'%s: [%s] %s' % (nick, page, entry)
        except Exception, error:
            log.warn(u'error in module %s' % self.__module__)
            log.exception(error)
            return u"%s: Couldn't load the page LJ returned D:" % nick


if __name__ == u'__main__':
    from utils import test_module
    test_module(Main)
