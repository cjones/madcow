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

"""Interface for getting really stupid IRC quotes"""

import re
import random
from include.utils import Module, stripHTML
from include.useragent import geturl
import logging as log

class Bash(object):

    random = 'http://www.bash.org/?random'
    bynum = 'http://www.bash.org/?num'
    search = 'http://www.bash.org/?search=query&show=100'
    entries = re.compile('<p class="qt">(.*?)</p>', re.DOTALL)


class QDB(object):

    random = 'http://qdb.us/random'
    bynum = 'http://qdb.us/num'
    search = 'http://qdb.us/?search=query&limit=100&approved=1'
    entries = re.compile('<td[^>]+><p>(.*?)</p>', re.DOTALL)


class Limerick(object):

    random = 'http://www.limerickdb.com/?random'
    bynum = 'http://www.limerickdb.com/?num'
    search = 'http://www.limerickdb.com/?search=query&number=100'
    entries = re.compile('<div class="quote_output">\s*(.*?)\s*</div>',
                         re.DOTALL)


class Main(Module):

    pattern = re.compile('^\s*(bash|qdb|limerick)(?:\s+(\S+))?', re.I)
    require_addressing = True
    help = '<bash|qdb|limerick> [#|query] - get stupid IRC quotes'
    sources = {'bash': QDB(),
               'qdb': QDB(),
               'limerick': Limerick(),
               }
    _error = 'Having some issues, make some stupid quotes yourself'

    def response(self, nick, args, kwargs):
        try:
            source = self.sources[args[0]]
            try:
                query = args[1]
            except:
                query = None
            try:
                num = int(query)
                query = None
            except:
                num = None
            if num:
                url = source.bynum.replace('num', str(num))
            elif query:
                url = source.search.replace('query', query)
            else:
                url = source.random
            doc = geturl(url)
            entries = source.entries.findall(doc)
            if query:
                entries = [entry for entry in entries if query in entry]
            if len(entries) > 1:
                entry = random.choice(entries)
            else:
                entry = entries[0]
            return stripHTML(entry)
        except Exception, error:
            log.warn('error in module %s' % self.__module__)
            log.exception(error)
            return '%s: %s' % (nick, self._error)


if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)
