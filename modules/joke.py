#!/usr/bin/env python
#
# Copyright (C) 2007, 2008 Christopher Jones and James Johnston
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

"""Get a random joke"""

from include.utils import Module, stripHTML
from include.useragent import geturl
import re
from urlparse import urljoin
import urllib
import logging as log

class Main(Module):
    pattern = re.compile(r'^\s*joke(?:\s+(.+?))?\s*$', re.I)
    require_addressing = True
    help = 'joke <oneliners | news | signs | nerd | professional | quotes | lightbulb | couples | riddles | religion | gross | blonde | politics | doit | laws | defs | dirty | ethnic | zippergate> - displays a random joke'
    baseurl = 'http://www.randomjoke.com/topic/'
    random_url = urljoin(baseurl, 'haha.php')
    joke = re.compile(r'next.joke.*?<P>(.*?)<CENTER>', re.DOTALL)

    def response(self, nick, args, kwargs):
        query = args[0]
        if query is None or query == '':
            url = self.random_url
        else:
            query = ' '.join(query.split())
            query = query.replace(' ', '_')
            query = urllib.quote(query) + '.php'
            url = urljoin(self.baseurl, query)
        try:
            doc = geturl(url)
            result = self.joke.findall(doc)[0]
            result = stripHTML(result)

            # cleanup output a bit.. some funny whitespace in it -cj
            result = result.replace('\x14', ' ')
            result = result.replace('\n', ' ')
            result = re.sub(r'\s{2,}', ' ', result)
            result = result.strip()

            return '%s' % result
        except Exception, e:
            log.warn('error in %s: %s' % (self.__module__, e))
            log.exception(e)
            return "%s: I had a problem with that, sorry." % nick


if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)
