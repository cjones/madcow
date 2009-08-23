#!/usr/bin/env python
#
# Copyright (C) 2007-2008 Chris Jones
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

"""Translation service using Google Translate"""

from include.utils import Module
import logging as log
import re
from include.useragent import geturl
from include import simplejson

__version__ = '2.0'
__author__ = 'Chris Jones <cjones@gruntle.org>'
__all__ = []

class BabelError(Exception):

    """Raised to stop translation due to internal error"""


class Main(Module):

    """Translation service using Google Translate"""

    pattern = r'^\s*(tr(?:ans(?:late)?)?(.+?)|list\s+lang(s|uages))\s*$'
    pattern = re.compile(pattern, re.I)
    help = 'translate <lang> to <lang> [to <lang> ...]: text'
    help += '\nlist languages - show all translate languages'
    default_lang = 'english'
    url = 'http://ajax.googleapis.com/ajax/services/language/translate'

    # synced with google.language Sun Aug 23 10:50:03 PDT 2009
    langs = {'albanian': 'sq',
             'arabic': 'ar',
             'bulgarian': 'bg',
             'catalan': 'ca',
             'chinese': 'zh-CN',
             'chinese-traditional': 'zh-TW',
             'croatian': 'hr',
             'czech': 'cs',
             'danish': 'da',
             'dutch': 'nl',
             'english': 'en',
             'estonian': 'et',
             'filipino': 'tl',
             'finnish': 'fi',
             'french': 'fr',
             'galician': 'gl',
             'german': 'de',
             'greek': 'el',
             'hebrew': 'iw',
             'hindi': 'hi',
             'hungarian': 'hu',
             'indonesian': 'id',
             'italian': 'it',
             'japanese': 'ja',
             'korean': 'ko',
             'latvian': 'lv',
             'lithuanian': 'lt',
             'maltese': 'mt',
             'norwegian': 'no',
             'persian': 'fa',
             'polish': 'pl',
             'portuguese': 'pt',
             'romanian': 'ro',
             'russian': 'ru',
             'serbian': 'sr',
             'slovak': 'sk',
             'slovenian': 'sl',
             'spanish': 'es',
             'swedish': 'sv',
             'thai': 'th',
             'turkish': 'tr',
             'ukrainian': 'uk',
             'vietnamese': 'vi'}

    def response(self, nick, args, kwargs):
        """Return a response to the bot to display"""
        if args[0].startswith('tr'):
            try:
                message = self.parse(args[1])
            except BabelError, error:
                log.error(error)
                message = error
            except Exception, error:
                log.warn('error in %s' % self.__module__)
                log.exception(error)
                message = error
        else:
            message = ', '.join(self.langs)
        return u'%s: %s' % (nick, message)

    def parse(self, cmd):
        """Parse command structure and transform text"""
        if ':' not in cmd:
            raise BabelError('missing text to translate')
        cmd, text = [arg.strip() for arg in cmd.split(':', 1)]
        cmd = cmd.lower().split()

        translations = []
        current_lang = None
        while cmd:
            arg = cmd.pop(0)
            if arg == 'from':
                continue
            elif arg in self.langs:
                if current_lang:
                    if arg == 'auto':
                        raise BabelError('can only auto-detect source')
                    if current_lang != arg:
                        job = self.langs[current_lang], self.langs[arg]
                        translations.append(job)
                current_lang = arg
            elif arg == 'to':
                if not current_lang:
                    current_lang = 'auto'
            else:
                raise BabelError('unknown language: ' + arg)

        if not translations:
            translations = [('auto', self._default_lang)]
        for from_lang, to_lang in translations:
            text = self.translate(text, from_lang, to_lang)
        return text

    def translate(self, text, src, dst):
        """Perform the translation"""
        opts = {'langpair': '%s|%s' % (src, dst), 'v': '1.0', 'q': text}
        res = simplejson.loads(geturl(self.url, opts))
        return res['responseData']['translatedText']


if __name__ == u'__main__':
    from include.utils import test_module
    test_module(Main)
