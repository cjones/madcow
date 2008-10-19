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
from include.utils import stripHTML, cache_property
import urlparse

__version__ = '0.1'
__author__ = 'Chris Jones <cjones@gruntle.org>'
__all__ = []

class BabelError(Exception):

    """Raised to stop translation due to internal error"""


class Main(Module):

    """Translation service using Google Translate"""

    pattern = Module._any
    help = 'translate <lang> to <lang> [to <lang> ...]: text'
    pattern = r'^\s*(trans(?:late)?(.+?)|list\s+lang(s|uages))\s*$'
    pattern = re.compile(pattern, re.I)
    _baseurl = 'http://translate.google.com/'
    _translate = urlparse.urljoin(_baseurl, '/translate_a/t')
    _langs_re = re.compile(r'<select name=sl.*?>(.*?)</select>')
    _lang_re = re.compile(r'<option.*?value="(.*?)".*?>(.*?)</option>')
    _lang_timeout = 1 * 60 * 60
    _default_lang = 'english'

    def response(self, nick, args, kwargs):
        if args[0].startswith('trans'):
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
        return '%s: %s' % (nick, message)

    def parse(self, cmd):
        """Parse command structure and transform text"""
        if ':' not in cmd:
            raise BabelError('missing text to translate')
        cmd, text = map(str.strip, cmd.split(':'))
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
                        translations.append((current_lang, arg))
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

    def translate(self, text, from_lang, to_lang):
        """Perform the translation"""
        opts = dict(client='t',
                    text=text,
                    sl=self.langs[from_lang],
                    tl=self.langs[to_lang])

        # ajax response
        data = geturl(self._translate, opts=opts)
        exec('data = ' + data)
        if isinstance(data, list):
            data = data[0]
        return data

    @cache_property(_lang_timeout)
    def langs(self):
        """Get available languages"""
        data = geturl(self._baseurl)
        try:
            data = self._langs_re.search(data).group(1)
        except AttributeError:
            raise BabelError("couldn't find langs")
        langs = {}
        for lang in self._lang_re.findall(data):
            code, name = map(str.lower, lang)
            if name == 'detect language':
                name = 'auto'
            langs[name] = code
        return langs


if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)
