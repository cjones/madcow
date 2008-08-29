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

"""JESUS!"""

import re
from include.utils import Module, stripHTML
from include.useragent import geturl
from urlparse import urljoin
import logging as log

class Main(Module):
    pattern = re.compile('^\s*bible\s+(\S+\s+\d+:[0-9-]+)', re.I)
    require_addressing = True
    help = 'bible <book> <chp>:<verse>[-<verse>] - spam jesus stuff'
    baseurl = 'http://www.biblegateway.com/'
    passage = urljoin(baseurl, '/passage/')
    verse = re.compile('<div class="result-text-style-normal">(.*?)</div>',
            re.DOTALL)
    footnotes = re.compile('<strong>Footnotes:</strong>.*$', re.DOTALL)
    junk_html = re.compile(r'<(h4|h5|span|sup|strong|ol|a).*?</\1>', re.I)
    max = 800

    def response(self, nick, args, kwargs):
        query = args[0]

        try:
            doc = geturl(self.passage, opts={'search': query, 'version': 31})
            response = self.verse.search(doc).group(1)
            response = self.footnotes.sub('', response)
            response = self.junk_html.sub('', response)
            response = stripHTML(response)
            response = response.strip()
            return response[:self.max]
        except Exception, e:
            log.warn('error in %s: %s' % (self.__module__, e))
            log.exception(e)
            return "%s: God didn't like that." % nick


if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)
