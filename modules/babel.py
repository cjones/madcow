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
from include import encoding

__version__ = u'0.1'
__author__ = u'Chris Jones <cjones@gruntle.org>'
__all__ = []

class BabelError(Exception):

    """Raised to stop translation due to internal error"""


class Main(Module):

    """Translation service using Google Translate"""

    pattern = r'^\s*(trans(?:late)?(.+?)|list\s+lang(s|uages))\s*$'
    pattern = re.compile(pattern, re.I)
    help = u'translate <lang> to <lang> [to <lang> ...]: text'
    help += u'\nlist languages - show all translate languages'
    _baseurl = u'http://translate.google.com/'
    _translate = urlparse.urljoin(_baseurl, u'/translate_a/t')
    _langs_re = re.compile(r'<select name=sl.*?>(.*?)</select>')
    _lang_re = re.compile(r'<option.*?value="(.*?)".*?>(.*?)</option>')
    _lang_timeout = 1 * 60 * 60
    _default_lang = u'english'

    def response(self, nick, args, kwargs):
        """Return a response to the bot to display"""
        if args[0].startswith(u'trans'):
            try:
                message = self.parse(args[1])
            except BabelError, error:
                log.error(error)
                message = error
            except Exception, error:
                log.warn(u'error in %s' % self.__module__)
                log.exception(error)
                message = error
        else:
            message = u', '.join(self.langs)
        return u'%s: %s' % (nick, message)

    def parse(self, cmd):
        """Parse command structure and transform text"""
        if u':' not in cmd:
            raise BabelError(u'missing text to translate')
        cmd, text = [arg.strip() for arg in cmd.split(u':', 1)]
        cmd = cmd.lower().split()

        translations = []
        current_lang = None
        while cmd:
            arg = cmd.pop(0)
            if arg == u'from':
                continue
            elif arg in self.langs:
                if current_lang:
                    if arg == u'auto':
                        raise BabelError(u'can only auto-detect source')
                    if current_lang != arg:
                        translations.append((current_lang, arg))
                current_lang = arg
            elif arg == u'to':
                if not current_lang:
                    current_lang = u'auto'
            else:
                raise BabelError(u'unknown language: ' + arg)

        if not translations:
            translations = [(u'auto', self._default_lang)]
        for from_lang, to_lang in translations:
            text = self.translate(text, from_lang, to_lang)
        return text

    def translate(self, text, from_lang, to_lang):
        """Perform the translation"""
        opts = dict(client=u't',
                    text=text,
                    sl=self.langs[from_lang],
                    tl=self.langs[to_lang])

        # ajax response
        data = geturl(self._translate, opts=opts)
        exec(u'data = ' + data)
        if isinstance(data, list):
            data = data[0]
        data = encoding.convert(data)
        return data

    @cache_property(_lang_timeout)
    def langs(self):
        """Get available languages"""
        data = geturl(self._baseurl)
        try:
            data = self._langs_re.search(data).group(1)
        except AttributeError:
            raise BabelError(u"couldn't find langs")
        langs = {}
        for lang in self._lang_re.findall(data):
            code, name = map(unicode.lower, lang)
            if name == u'detect language':
                name = u'auto'
            langs[name] = code
        return langs


if __name__ == u'__main__':
    from include.utils import test_module
    test_module(Main)
