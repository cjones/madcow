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

"""Spellcheck using google"""

from urlparse import urljoin

import re

from madcow.util import Module, strip_html
from madcow.util.http import getsoup

__version__ = '2.0'
__author__ = 'cj_ <cjones@gruntle.org>'

class Main(Module):

    pattern = re.compile(r'^\s*spell(?:\s*check)?\s+(.+?)\s*$', re.I)
    help = u'spellcheck <word> - use google to spellcheck'

    google_url = 'http://www.google.com/'
    google_search = urljoin(google_url, '/search')

    def response(self, nick, args, kwargs):
        try:
            opts = {'hl': 'en', 'aq': 'f', 'safe': 'off', 'q': args[0]}
            soup = getsoup(self.google_search, opts, referer=self.google_url)
            a = soup.body.find('a', 'spell')
            if a:
                res = strip_html(a.renderContents().decode('utf-8', 'ignore'))
            else:
                res = u'spelled correctly'
        except Exception, error:
            self.log.warn('error in module %s' % self.__module__)
            self.log.exception(error)
            res = u'I had trouble with that'
        return u'%s: %s' % (nick, res)

if __name__ == u'__main__':
    from madcow.util import test_module
    test_module(Main)
