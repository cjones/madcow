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

"""Get a random offensive ASCII art"""

from include.utils import Module, stripHTML
from include.useragent import geturl
import re
from urlparse import urljoin
import random
import urllib
import logging as log

class Main(Module):

    pattern = re.compile(r'^\s*artfart(?:\s+(.+?))?\s*$', re.I)
    require_addressing = True
    help = u'artfart - displays some offensive ascii art'
    baseurl = u'http://www.asciiartfarts.com/'
    random_url = urljoin(baseurl, u'random.cgi')
    artfart = re.compile(r'<h1>#<a href="\S+.html">\d+</a>: (.*?)</h1>.*?<pre'
                         r'>(.*?)</pre>', re.DOTALL)

    def response(self, nick, args, kwargs):
        query = args[0]
        if query is None or query == u'':
            url = self.random_url
        else:
            query = u' '.join(query.split())
            query = query.replace(u' ', u'_')
            query = urllib.quote(query) + u'.html'
            url = urljoin(self.baseurl, query)
        try:
            doc = geturl(url)
            results = self.artfart.findall(doc)
            result = random.choice(results)
            title, art = result
            art = stripHTML(art)
            return u'>>> %s <<<\n%s' % (title, art)
        except Exception, error:
            log.warn(u'error in module %s' % self.__module__)
            log.exception(error)
            return u"%s: I had a problem with that, sorry." % nick


if __name__ == u'__main__':
    from include.utils import test_module
    test_module(Main)
