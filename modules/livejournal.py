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

"""get a random lj"""

import re
from include import rssparser
from include.utils import Module, stripHTML, isUTF8
from include.useragent import geturl
from urlparse import urljoin
import logging as log

class Main(Module):

    enabled = True
    pattern = re.compile('^\s*(?:livejournal|lj)(?:\s+(\S+))?')
    require_addressing = True
    help = 'lj [user] - get latest entry to an lj, omit user for a random one'
    baseURL = 'http://livejournal.com'
    randomURL = urljoin(baseURL, '/random.bml')
    max = 800

    def response(self, nick, args, kwargs):
        try:
            try:
                user = args[0]
            except:
                user = None
            if user is None or user == '':
                doc = geturl(self.randomURL)
                user = re.search('"currentJournal": "(.*?)"', doc).group(1)
            url = urljoin(self.baseURL, '/users/%s/data/rss' % user)
            feed = rssparser.parse(url)

            # get latest entry and their homepage url
            entry, page = map(stripHTML, map(
                lambda x: x.encode(feed.encoding),
                [feed.entries[0].description, feed.channel.link]))

            # these can get absurdly long
            entry = entry[:self.max]

            return '%s: [%s] %s' % (nick, page, entry)

        except Exception, e:
            log.warn('error in %s: %s' % (self.__module__, e))
            log.exception(e)
            return "%s: Couldn't load the page LJ returned D:" % nick


if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)
