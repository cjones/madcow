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

"""Look up word definitions"""

from urlparse import urljoin
from urllib import quote
import logging as log
import re

from include.utils import Module
from include.useragent import getsoup
from include.utils import stripHTML

__version__ = '2.0'
__author__ = 'Chris Jones <cjones@gruntle.org>'
__all__ = []

class Main(Module):

    pattern = re.compile(r'^\s*def(?:ine)?\s+(.+?)\s*$', re.I)
    help = 'define <term> - get a definition'
    base_url = 'http://definr.com/'
    define_url = urljoin(base_url, '/definr/show/toe')
    whitespace_re = re.compile(r'\s{2,}')

    def response(self, nick, args, kwargs):
        try:
            response = self.lookup(args[0])
        except Exception, error:
            log.warn('error in module %s' % self.__module__)
            log.exception(error)
            response = 'Stop making words up'
        return u'%s: %s' % (nick, response)

    def lookup(self, term, idx=1):
        """Lookup term in dictionary"""
        url = urljoin(self.define_url, quote(term.lower()))
        soup = getsoup(url, referer=self.base_url)
        for br in soup('br'):
            br.extract()
        val = stripHTML(soup.renderContents().decode('utf-8'))
        val = val.replace(u'\xa0', ' ').replace('\n', ' ')
        return self.whitespace_re.sub(' ', val).strip()


if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)
