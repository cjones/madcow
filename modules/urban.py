#!/usr/bin/env python
#
# Copyright (C) 2007-2008 Christopher Jones
#
# This file is part of Madcow.
#
# Madcow is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# Madcow is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License
# along with Madcow.  If not, see <http://www.gnu.org/licenses/>.

"""Module stub"""

import logging as log
import re

from include.utils import Module, stripHTML
from include.useragent import getsoup
from urlparse import urljoin

__version__ = '2.0'
__author__ = 'Chris Jones <cjones@gruntle.org>'
__all__ = []

class Main(Module):

    pattern = re.compile(r'^\s*urban\s+(.+?)(?:\s+(\d+))?\s*$', re.I)
    help = 'urban <term> [#] - lookup word/phrase on urban dictionary'

    urban_url = 'http://www.urbandictionary.com/'
    urban_search = urljoin(urban_url, 'define.php')
    entry_re = re.compile(r'entry_\d+')
    newline_re = re.compile(r'(?:\r\n|[\r\n])')

    RESULTS_PER_PAGE = 7

    def response(self, nick, args, kwargs):
        try:
            query, idx = args
            if idx:
                idx = int(idx)
            response = self.lookup(query, idx)
        except Exception, error:
            log.warn(u'error in module %s' % self.__module__)
            log.exception(error)
            response = u'So obscure, not even urban dictionary knows it'
        return u'%s: %s' % (nick, response)

    def lookup(self, query, idx=None):
        """Look up term on urban dictionary"""
        if idx is None:
            idx = 1
        page = int(idx / self.RESULTS_PER_PAGE)
        idx = (idx % self.RESULTS_PER_PAGE) - 1
        if idx == -1:
            idx = 6
        soup = getsoup(self.urban_search, {'term': query, 'page': page},
                       referer=self.urban_url)
        table = soup.body.find('table', id='entries')
        entry = table('td', 'text', id=self.entry_re)[idx]
        result = self.render(entry.find('div', 'definition'))
        try:
            example = self.render(entry.find('div', 'example'))
            result += u' - Example: %s' % example
        except:
            pass
        return result

    @staticmethod
    def render(node):
        """Render node to text"""
        data = node.renderContents()
        if isinstance(data, str):
            data = data.decode('utf-8', 'ignore')
        return Main.newline_re.sub(' ', stripHTML(data)).strip()

if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)
