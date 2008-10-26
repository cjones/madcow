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

"""Get traffic info from CHP website (bay area only)"""

import re
from include.utils import Module, stripHTML
from include.useragent import geturl
import logging as log

class Main(Module):

    pattern = re.compile('^\s*chp\s+(.+)', re.I)
    require_addressing = True
    help = 'chp <highway> - look for CHP reports for highway, such as 101'
    url = 'http://cad.chp.ca.gov/sa_list.asp?centerin=GGCC&style=l'
    incidents = re.compile('<tr>(.*?)</tr>', re.DOTALL)
    data = re.compile('<td class="T".*?>(.*?)</td>')
    clean = re.compile('[^0-9a-z ]', re.I)

    def response(self, nick, args, kwargs):
        query = args[0]
        try:
            check = self.clean.sub('', query)
            check = re.compile(check, re.I)
            results = []
            doc = geturl(self.url)
            for i in self.incidents.findall(doc):
                data = [stripHTML(c) for c in self.data.findall(i)][1:]
                if len(data) != 4:
                    continue
                if check.search(data[2]):
                    results.append('=> %s: %s - %s - %s' % (data[0], data[1],
                        data[2], data[3]))

            if len(results) > 0:
                return '\n'.join(results)
            else:
                return '%s: No incidents found' % nick
        except Exception, error:
            log.warn('error in module %s' % self.__module__)
            log.exception(error)
            return '%s: I failed to perform that lookup' % nick


if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)
