"""Handles WikiMedia queries"""

from BeautifulSoup import BeautifulSoup
from madcow.util.http import geturl
from madcow.util import strip_html, Module
from urlparse import urljoin
import re

# wiki configuration
WIKIS = {'wikipedia': {
             'keys': ['wp', 'wiki', 'wikipedia'],
             'baseurl': 'http://en.wikipedia.org/',
             'kwargs': {
                 'random': '/wiki/Special:Random',
                 'search': '/wiki/Special:Search',
                 'advert': ' - Wikipedia, the free encyclopedia',
                 'error': 'Search results',
                 },
             },
         'conservapedia': {
             'keys': ['cp'],
             'baseurl': 'http://www.conservapedia.com/',
             'kwargs': {
                 'random': '/Special:Random',
                 'search': '/Special:Search',
                 'advert': ' - Conservapedia',
                 'error': 'Search results',
                 },
             },
         'christopedia': {
             'keys': ['ch'],
             'baseurl': 'http://christopedia.us/',
             'kwargs': {
                 'random': '/Special:Random',
                 'search': '/Special:Search',
                 'advert': ' - Christopedia, the Christian encyclopedia',
                 'error': 'Search results',
                 },
             },
         'encyclopediadramatica': {
             'keys': ['ed', 'drama'],
             'baseurl': 'http://encyclopediadramatica.com/',
             'kwargs': {
                 'random': '/Special:Random',
                 'search': '/Special:Search',
                 'advert': ' - Encyclopedia Dramatica',
                 'error': 'Search results',
                 },
             },
         }

class WikiMedia(object):

    citations_re = re.compile(r'\[.*?\]', re.DOTALL)
    parens_re = re.compile(r'\(.*?\)', re.DOTALL)
    whitespace_re = re.compile(r'[ \t\r\n]+')
    fix_punc_re = re.compile(r'\s+([,;:.])')
    sentence_re = re.compile(r'(.*?\.)\s+', re.DOTALL)
    summary_size = 400
    scripts_re = re.compile(r'<script [^>]+>.*?</script>', re.I | re.DOTALL)

    def __init__(self, baseurl, **kwargs):
        self.baseurl = baseurl
        self.__dict__.update(kwargs)

    def getsummary(self, query):
        if not self.search:
            return u"i don't know how to search this wiki!"
        opts = {'search': query, 'go': 'Go'}
        return self._getsummary(self.search_url, opts=opts)

    def getrandom(self):
        if not self.random:
            return u"i don't know where random pages are on this wiki!"
        return self._getsummary(self.random_url)

    def _getsummary(self, url, opts=None):
        soup, title = self._getpage(url, opts)

        spam = soup.find('div', attrs={'id': 'siteNotice'})
        if spam is not None:
            spam.extract()

        # massage into plain text by concatenating paragraphs
        content = ' '.join(p.renderContents().decode('utf-8')
                           for p in soup.findAll('p'))

        # clean up rendered text
        content = strip_html(content)                    # strip markup
        content = self.citations_re.sub(u'', content)   # remove citations
        content = self.parens_re.sub(u'', content)      # remove parentheticals
        content = self.whitespace_re.sub(u' ', content) # compress whitespace
        content = self.fix_punc_re.sub(r'\1', content)  # fix punctuation
        content = content.strip()                       # strip whitespace

        # generate summary by adding as many sentences as possible before limit
        summary = u'%s -' % title
        for sentence in self.sentence_re.findall(content):
            if len(summary + sentence) >= self.summary_size:
                break
            summary += ' ' + sentence
        return summary

    def _getpage(self, url, opts=None):
        page = geturl(url, referer=self.baseurl, opts=opts)
        # HTMLParser doesn't handle this very well.. see:
        # http://www.crummy.com/software/BeautifulSoup/3.1-problems.html
        page = self.scripts_re.sub('', page)
        soup = BeautifulSoup(page)

        # get page title
        title = soup.title.string
        if self.advert and self.advert in title:
            title = title.replace(self.advert, '')

        # remove all tabular data/sidebars
        for table in soup.findAll('table'):
            table.extract()

        # remove disambiguation links
        for div in soup.findAll('div', 'dablink'):
            div.extract()

        # remove latitude/longitude metadata for places
        for span in soup.findAll('span', id='coordinates'):
            span.extract()

        # strip non-english content wrappers
        for span in soup.findAll('span', lang=True):
            span.extract()

        # remove IPA pronounciation guidelines
        for span in soup.findAll('span', 'IPA'):
            span.extract()
        for a in soup.findAll('a', text='IPA'):
            a.extract()
        for span in soup.findAll('span', 'audiolink'):
            span.extract()

        return soup, title

    @property
    def search_url(self):
        return urljoin(self.baseurl, self.search)

    @property
    def random_url(self):
        return urljoin(self.baseurl, self.random)


def make_help(wikis):
    """Generate madcow help from wiki config"""
    help = []
    for wiki, opts in wikis.iteritems():
        item = []
        if len(opts['keys']) > 1:
            item.append('<')
        item.append('|'.join(opts['keys']))
        if len(opts['keys']) > 1:
            item.append('>')
        if opts['kwargs']['search']:
            item.append(' ')
        if opts['kwargs']['random']:
            item.append('[')
        else:
            item.append('<')
        item.append('query')
        if opts['kwargs']['random']:
            item.append(']')
        else:
            item.append('>')
        item.append(' - search ' + wiki)
        help.append(''.join(item))
    return '\n'.join(help)


class Main(Module):

    """Autoloaded by Madcow"""

    pattern = Module._any
    terminate = False
    help = make_help(WIKIS)
    match_fmt = r'^\s*(?:%s)(?:\s+(.+?))?\s*$'

    def init(self):
        self.wikis = {}
        for wiki, opts in WIKIS.iteritems():
            match_re = self.match_fmt % '|'.join(opts['keys'])
            match_re = re.compile(match_re, re.I)
            handler = WikiMedia(opts['baseurl'], **opts['kwargs'])
            self.wikis[wiki] = {'match_re': match_re, 'handler': handler}

    def response(self, nick, args, kwargs):
        message = args[0]
        for wiki, opts in self.wikis.iteritems():
            try:
                query = opts['match_re'].search(message).group(1)
                if query:
                    response = opts['handler'].getsummary(query)
                else:
                    response = opts['handler'].getrandom()
                if response:
                    return u'%s: %s' % (nick, response)
            except AttributeError:
                pass
