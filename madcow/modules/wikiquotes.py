"""Plugin to return random quote from WikiQuotes"""

from urlparse import urljoin

import random
import re

from BeautifulSoup import BeautifulSoup
from madcow.util import strip_html, Module


class Main(Module):

    base_url = u'http://en.wikiquote.org/'
    advert = u' - Wikiquote'

    pattern = re.compile(r'^\s*(?:wikiquote|wq)\s*(?:\s+(.*?)\s*)?$', re.I)
    _linebreak = re.compile(r'[\r\n]+')
    _whitespace = re.compile(r'\s{2,}')
    _author = u'random'
    _max = 10

    require_addressing = True
    help = u'wikiquote - get random quote from wikiquotes'

    # site-specific details, default is english wikipedia
    random_path = u'/wiki/Special:Random'
    search_path = u'/wiki/Special:Search'
    error = u'Search results'

    # size of response
    summary_size = 400
    sample_size = 32 * 1024

    # precompiled regex
    _citations = re.compile(r'\[.*?\]', re.DOTALL)
    _audio = re.compile(r'audiolink', re.I)
    _parens = re.compile(r'\(.*?\)', re.DOTALL)
    _whitespace = re.compile(r'[ \t\r\n]+')
    _sentence = re.compile(r'(.*?\.)\s+', re.DOTALL)
    _fix_punc = re.compile(r'\s+([,;:.])')

    def get_summary(self, query):
        soup, title = self.get_soup(query)

        # check if this is a disambiguation page, if so construct special page
        # there isn't a consistent style guide, so we just try to do the
        # most common format (ordered list of links). if this fails, return
        # a friendly failure for now
        if soup.find(u'div', attrs={u'id': u'disambig'}):
            try:
                summary = u'%s (Disambiguation) - ' % title
                for link in soup.find(u'ul').findAll(u'a'):
                    title = unicode(link[u'title']).strip()
                    if len(summary) + len(title) + 2 > self.summary_size:
                        break
                    if not summary.endswith(u' '):
                        summary += u', '
                    summary += title
            except:
                summary = u'Fancy, unsupported disambiguation page!'
            return summary

        # massage into plain text by concatenating paragraphs
        content = []
        for para in soup.findAll(u'p'):
            content.append(unicode(para))
        content = u' '.join(content)

        # clean up rendered text
        content = strip_html(content)                 # strip markup
        content = self._citations.sub(u'', content)   # remove citations
        content = self._parens.sub(u'', content)      # remove parentheticals
        content = self._whitespace.sub(u' ', content) # compress whitespace
        content = self._fix_punc.sub(r'\1', content) # fix punctuation
        content = content.strip()                    # strip whitespace

        # search error
        if title == self.error:
            return u'No results found for "%s"' % query

        # generate summary by adding as many sentences as possible before limit
        summary = u'%s -' % title
        for sentence in self._sentence.findall(content):
            if len(summary) + 1 + len(sentence) > self.summary_size:
                break
            summary += u' %s' % sentence
        return summary

    def get_soup(self, query):
        if isinstance(query, (list, tuple)):
            query = u' '.join(query)

        # load page
        if query == u'random':
            opts = {}
            url = urljoin(self.base_url, self.random_path)
        else:
            opts = {u'search': query, u'go': u'Go'}
            url = urljoin(self.base_url, self.search_path)
        page = self.geturl(url, referer=self.base_url, opts=opts, size=self.sample_size)

        # create BeautifulSoup document tree
        soup = BeautifulSoup(page)

        # extract title minus WP advert
        title = soup.title.string.replace(self.advert, u'')

        # remove all tabular data/sidebars
        for table in soup.findAll(u'table'):
            table.extract()

        # remove disambiguation links
        for dablink in soup.findAll(u'div', attrs={u'class': u'dablink'}):
            dablink.extract()

        # remove latitude/longitude metadata for places
        for coord in soup.findAll(u'span', attrs={u'id': u'coordinates'}):
            coord.extract()

        # strip non-english content wrappers
        for span in soup.findAll(u'span', attrs={u'lang': True}):
            span.extract()

        # remove IPA pronounciation guidelines
        for span in soup.findAll(u'span', attrs={u'class': u'IPA'}):
            span.extract()
        for link in soup.findAll(u'a', text=u'IPA'):
            link.extract()
        for span in soup.findAll(u'span', attrs={u'class': self._audio}):
            span.extract()

        return soup, title

    def get_random_quote(self, author=_author, max=_max):
        for i in range(0, max):
            try:
                return self._get_random_quote(author=author)
            except:
                raise
                pass
        raise Exception(u'no parseable page found :(')

    def extract_quote(self, obj):
        li = obj.find(u'li')
        contents = li.contents
        contents = [unicode(part) for part in contents]
        quote = u' '.join(contents)
        quote = strip_html(quote)
        quote = self._linebreak.sub(u' ', quote)
        quote = self._whitespace.sub(u' ', quote)
        quote = quote.strip()
        return quote

    def _get_random_quote(self, author=_author):
        soup, title = self.get_soup(author)
        if title == self.error:
            return u"Couldn't find quotes for that.."
        content = soup.find(u'div', attrs={u'id': u'mw-content-text'})
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
        author = args[0]
        if author:
            max = 1
        else:
            author = _author
            max = _max
        return self.get_random_quote(author=author, max=max)
