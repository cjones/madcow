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

    pattern = re.compile(u'^\s*bible\s+(\S+\s+\d+:[0-9-]+)', re.I)
    require_addressing = True
    help = u'bible <book> <chp>:<verse>[-<verse>] - spam jesus stuff'
    baseurl = u'http://www.biblegateway.com/'
    passage = urljoin(baseurl, u'/passage/')
    verse = re.compile(u'<div class="result-text-style-normal">(.*?)</div>',
                       re.DOTALL)
    footnotes = re.compile(u'<strong>Footnotes:</strong>.*$', re.DOTALL)
    junk_html = re.compile(r'<(h4|h5|span|sup|strong|ol|a).*?</\1>', re.I)
    max = 800

    def response(self, nick, args, kwargs):
        query = args[0]
        try:
            doc = geturl(self.passage, opts={u'search': query, u'version': 31})
            response = self.verse.search(doc).group(1)
            response = self.footnotes.sub(u'', response)
            response = self.junk_html.sub(u'', response)
            response = stripHTML(response)
            response = response.strip()
            return response[:self.max]
        except Exception, error:
            log.warn(u'error in module %s' % self.__module__)
            log.exception(error)
            return u"%s: God didn't like that." % nick


if __name__ == u'__main__':
    from include.utils import test_module
    test_module(Main)
