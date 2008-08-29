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
_base_url = 'http://en.wikiquote.org/'
_advert = ' - Wikiquote'
_linebreak = re.compile(r'[\r\n]+')
_whitespace = re.compile(r'\s{2,}')
_author = 'random'
_max = 10

class Main(Module):
    pattern = _pattern
    require_addressing = True
    help = 'wikiquote - get random quote from wikiquotes'

    def __init__(self, madcow=None):
        self.wiki = Wiki(base_url=_base_url, advert=_advert)

    def get_random_quote(self, author=_author, max=_max):
        for i in range(0, max):
            try:
                return self._get_random_quote(author=author)
            except:
                pass
        raise Exception, 'no parseable page found :('

    def extract_quote(self, obj):
        li = obj.find('li')
        contents = li.contents
        contents = [str(part) for part in contents]
        quote = ' '.join(contents)
        quote = stripHTML(quote)
        quote = _linebreak.sub(' ', quote)
        quote = _whitespace.sub(' ', quote)
        quote = quote.strip()
        return quote

    def _get_random_quote(self, author=_author):
        soup, title = self.wiki.get_soup(author)
        if title == Wiki._error:
            return "Couldn't find quotes for that.."
        content = soup.find('div', attrs={'id': 'bodyContent'})
        uls = content.findAll('ul', recursive=False)
        quotes = []
        for ul in uls:
            note = ul.find('ul')
            if note:
                note.extract()
                note = self.extract_quote(note)
            quote = self.extract_quote(ul)
            if note:
                quote = '%s -- %s' % (quote, note)
            quotes.append(quote)
        quote = random.choice(quotes)
        quote = '%s: %s' % (title, quote)
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
        except Exception, e:
            log.warn('error in %s: %s' % (self.__module__, e))
            log.exception(e)
            return '%s: problem with query: %s' % (nick, e)


if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)
