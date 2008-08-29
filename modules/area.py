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

"""This module looks up area codes and returns the most likely city"""

import re
from include.utils import Module
from include.useragent import geturl
from urlparse import urljoin
import logging as log

class Main(Module):
    pattern = re.compile('^\s*area(?:\s+code)?\s+(\d+)\s*', re.I)
    require_addressing = True
    help = 'area <areacode> - what city does it belong to'
    baseurl = 'http://www.melissadata.com/'
    searchurl = urljoin(baseurl, '/lookups/phonelocation.asp')
    city = re.compile(r'<tr><td><A[^>]+>(.*?)</a></td><td>(.*?)</td><td align=center>\d+</td></tr>')

    def response(self, nick, args, kwargs):
        try:
            geturl(self.baseurl)
            doc = geturl(self.searchurl, opts={'number': args[0]})
            city, state = self.city.search(doc).groups()
            city = ' '.join([x.lower().capitalize() for x in city.split()])
            return '%s: %s = %s, %s' % (nick, args[0], city, state)
        except Exception, e:
            log.warn('error in %s: %s' % (self.__module__, e))
            log.exception(e)
            return "%s: I couldn't look that up for some reason.  D:" % nick


if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)
