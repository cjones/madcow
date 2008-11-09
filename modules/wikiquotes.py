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

"""Plugin to return random quote from WikiQuotes"""

from include.wiki import Wiki
from include.utils import stripHTML, Module
import re
import random
import logging as log

_pattern = re.compile(r'^\s*(?:wikiquote|wq)\s*(?:\s+(.*?)\s*)?$', re.I)
_linebreak = re.compile(r'[\r\n]+')
_whitespace = re.compile(r'\s{2,}')
_author = u'random'
_max = 10

class WikiQuotes(Wiki):

    base_url = u'http://en.wikiquote.org/'
    advert = u' - Wikiquote'


class Main(Module):

    pattern = _pattern
    require_addressing = True
    help = u'wikiquote - get random quote from wikiquotes'

    def __init__(self, madcow=None):
        self.wiki = WikiQuotes()

    def get_random_quote(self, author=_author, max=_max):
        for i in range(0, max):
            try:
                return self._get_random_quote(author=author)
            except:
                pass
        raise Exception(u'no parseable page found :(')

    def extract_quote(self, obj):
        li = obj.find(u'li')
        contents = li.contents
        contents = [unicode(part) for part in contents]
        quote = u' '.join(contents)
        quote = stripHTML(quote)
        quote = _linebreak.sub(u' ', quote)
        quote = _whitespace.sub(u' ', quote)
        quote = quote.strip()
        return quote

    def _get_random_quote(self, author=_author):
        soup, title = self.wiki.get_soup(author)
        if title == self.wiki.error:
            return u"Couldn't find quotes for that.."
        content = soup.find(u'div', attrs={u'id': u'bodyContent'})
        uls = content.findAll(u'ul', recursive=False)
        quotes = []
        for ul in uls:
            note = ul.find(u'ul')
            if note:
                note.extract()
                note = self.extract_quote(note)
            quote = self.extract_quote(ul)
            if note:
                quote = u'%s -- %s' % (quote, note)
            quotes.append(quote)
        quote = random.choice(quotes)
        quote = u'%s: %s' % (title, quote)
        return quote

    def response(self, nick, args, kwargs):
        try:
            author = args[0]
            if author:
                max = 1
            else:
                author = _author
                max = _max
            return self.get_random_quote(author=author, max=max)
        except Exception, error:
            log.warn(u'error in module %s' % self.__module__)
            log.exception(error)
            return u'%s: problem with query: %s' % (nick, error)


if __name__ == u'__main__':
    log.root.setLevel(log.DEBUG)
    from include.utils import test_module
    test_module(Main)
