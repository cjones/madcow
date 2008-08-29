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

"""Use AV's babel translator for language conversion"""

import re
from include.utils import Module
from include.useragent import posturl
from urlparse import urljoin
import logging as log

class Main(Module):
    pattern = re.compile('^\s*(list languages|translate)(?:\s+from\s+(\w+)\s+to\s+(\w+)\s*[-:]\s*(.+))?$', re.I)
    require_addressing = True
    help = 'list languages - list translate languages available\n'
    help += 'translate from <lang> to <lang>: text'
    re_translate = re.compile(r'<div id="result"><div.*?>(.*?)</div>')
    languages = {
        'chinese-simp': 'zh',
        'chinese-trad': 'zt',
        'chinese': 'zh',
        'dutch': 'nl',
        'english': 'en',
        'french': 'fr',
        'german': 'de',
        'greek': 'el',
        'italian': 'it',
        'japanese': 'ja',
        'korean': 'ko',
        'portuguese': 'pt',
        'russian': 'ru',
        'spanish': 'es',
    }
    baseurl = 'http://babelfish.yahoo.com/'
    translate = urljoin(baseurl, '/translate_txt')
    unknown =  "I don't know that language, try: list languages"

    def response(self, nick, args, kwargs):
        try:
            if args[0] == 'list languages':
                return '%s: %s' % (nick, ', '.join(self.languages.keys()))

            try:
                from_lang = self.languages[args[1].lower()]
                to_lang = self.languages[args[2].lower()]
            except:
                return '%s: %s' % (nick, self.unknown)

            opts = {
                'ei': 'UTF-8',
                'doit': 'done',
                'fr': 'bf-home',
                'intl': '1',
                'tt': 'urltext',
                'trtext': args[3],
                'lp': '%s_%s' % (from_lang, to_lang),
                'btnTrTxt': 'Translate',
            }

            doc = posturl(self.translate, opts=opts)
            translated = self.re_translate.search(doc).group(1)
            return '%s: %s' % (nick, translated)
        except Exception, e:
            log.warn('error in %s: %s' % (self.__module__, e))
            log.exception(e)
            return "%s: Couldn't translate for some reason :/" % nick


if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)
