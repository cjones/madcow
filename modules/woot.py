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
from include import rssparser
from include.utils import Module, stripHTML
import logging as log

class Main(Module):

    pattern = re.compile('^\s*woot\s*$', re.I)
    require_addressing = True
    help = 'woot - get latest offer from woot.com'
    url = 'http://woot.com/Blog/Rss.aspx'
    max = 200
    break_re = re.compile(r'\s*[\r\n]+\s*')

    def response(self, nick, args, kwargs):
        try:
            rss = rssparser.parse(self.url)
            entry = rss.entries[3]
            title, summary, link = map(stripHTML, map(
                lambda x: x.encode(rss.encoding),
                [entry.title, entry.summary, entry.link]))
            summary = self.break_re.sub(' ', summary)
            if len(summary) > self.max:
                summary = summary[:self.max - 4] + ' ...'
            return '%s [%s] %s' % (title, link, summary)
        except Exception, error:
            log.warn('error in %s: %s' % (self.__module__, error))
            log.exception(error)
            return '%s: error reading woot page' % nick


if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)
