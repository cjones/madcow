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

"""Lookup a definition in the dictionary..."""

import re
from include.utils import stripHTML, Module
from include.useragent import geturl
from urlparse import urljoin
import logging as log

class Main(Module):

    pattern = re.compile('^\s*define\s+(\S+)(?:\s+(\d+))?$')
    require_addressing = True
    help = 'define <word/phrase> [#] - get a definition from merriam-webster'
    re_defs = re.compile(r'<div class="defs">(.*?)</div>', re.DOTALL)
    re_newline = re.compile(r'[\r\n]+')
    re_def_break = re.compile(r'<span class="sense_break"/>')
    header = re.compile('^.*?:\xa0')
    base_url = 'http://www.m-w.com/dictionary/'

    def response(self, nick, args, kwargs):
        word = args[0].lower()
        try:
            try:
                num = int(args[1])
            except:
                num = 1

            url = urljoin(self.base_url, word)
            doc = geturl(url)
            defs = self.re_defs.search(doc).group(1)
            defs = self.re_newline.sub('', defs)
            defs = self.re_def_break.split(defs)
            if len(defs) > 1:
                defs.pop(0)
            if num > len(defs):
                num = 1
            definition = defs[num - 1]
            definition = stripHTML(definition)
            definition = self.header.sub('', definition)

            return '%s: [%s/%s] %s' % (nick, num, len(defs), definition)

        except Exception, error:
            log.warn('error in %s: %s' % (self.__module__, error))
            log.exception(error)
            return "%s: I couldn't look that up for some reason.  D:" % nick


if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)
