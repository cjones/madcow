#!/usr/bin/env python

"""Plugin to return random quote from WikiQuotes"""

from include.wiki import Wiki
from include.utils import stripHTML, Base
import re
import random
import sys
import os

_pattern = re.compile(r'^\s*(?:wikiquote|wq)\s*(?:\s+(.*?)\s*)?$', re.I)
_base_url = 'http://en.wikiquote.org/'
_advert = ' - Wikiquote'
_linebreak = re.compile(r'[\r\n]+')
_whitespace = re.compile(r'\s{2,}')
_author = 'random'
_max = 10

class Main(Base):
    enabled = True
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

    def response(self, nick, args, **kwargs):
        try:
            author = args[0]
            if author:
                max = 1
            else:
                author = _author
                max = _max
            return self.get_random_quote(author=author, max=max)
        except Exception, e:
            return '%s: problem with query: %s' % (nick, e)


def main():
    try:
        main = Main()
        args = main.pattern.search(' '.join(sys.argv[1:])).groups()
        print main.response(nick=os.environ['USER'], args=args)
    except Exception, e:
        print 'no match: %s' % e

if __name__ == '__main__':
    sys.exit(main())
