#!/usr/bin/env python

"""Plugin to return random quote from WikiQuotes"""

from include.wiki import Wiki
from include.utils import stripHTML
import re
import random

_pattern = re.compile(r'^\s*wikiquote\s*(?:\s+(.*?)\s*)?$', re.I)
_base_url = 'http://en.wikiquote.org/'
_advert = ' - Wikiquote'
_summary_size = Wiki._summary_size
_sample_size = Wiki._sample_size
_linebreak = re.compile(r'[\r\n]+')
_whitespace = re.compile(r'\s{2,}')
_author = 'random'
_max = 10

class MatchObject(object):

    def __init__(self, *args, **kwargs):
        self.enabled = True
        self.pattern = _pattern
        self.requireAddressing = True
        self.thread = True
        self.wrap = False
        self.help = 'wikiquote - get random quote from wikiquotes'
        self.wiki = Wiki(base_url=_base_url, advert=_advert,
                summary_size=_summary_size, sample_size=_sample_size)

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

    def response(self, **kwargs):
        try:
            author = ' '.join(kwargs['args'])
            if author:
                max = 1
            else:
                author = _author
                max = _max
            return self.get_random_quote(author=author, max=max)
        except Exception, e:
            return '%s: problem with query: %s' % (kwargs['nick'], e)


if __name__ == '__main__':
    import os, sys
    print MatchObject().response(args=sys.argv[1:], nick=os.environ['USER'])
    sys.exit(0)
