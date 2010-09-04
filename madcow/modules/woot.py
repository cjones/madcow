#!/usr/bin/env python
#
# Copyright (C) 2007, 2008 Christopher Jones and Todd Dailey
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

"""get the current woot - author: Twid"""

import re
from include import feedparser
from include.utils import Module, stripHTML
import logging as log

class Main(Module):

    pattern = re.compile(u'^\s*woot\s*$', re.I)
    require_addressing = True
    help = u'woot - get latest offer from woot.com'
    url = u'http://woot.com/Blog/Rss.aspx'
    max = 200
    break_re = re.compile(r'\s*[\r\n]+\s*')

    def response(self, nick, args, kwargs):
        try:
            rss = feedparser.parse(self.url)
            entry = rss.entries[3]
            title, summary, link = map(
                    stripHTML, [entry.title, entry.summary, entry.link])
            summary = self.break_re.sub(u' ', summary)
            if len(summary) > self.max:
                summary = summary[:self.max - 4] + u' ...'
            return u'%s [%s] %s' % (title, link, summary)
        except Exception, error:
            log.warn(u'error in module %s' % self.__module__)
            log.exception(error)
            return u'%s: error reading woot page' % nick


if __name__ == u'__main__':
    from include.utils import test_module
    test_module(Main)
