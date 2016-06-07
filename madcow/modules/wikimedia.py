"""Handles WikiMedia queries"""

from BeautifulSoup import BeautifulSoup
from madcow.util import strip_html, Module
from madcow.util.text import *
from urlparse import urljoin
import re

class Main(Module):

    """Autoloaded by Madcow"""

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

    wikiconf = {
            'wikipedia': {
                'keys': ['wp', 'wiki', 'wikipedia'],
                'baseurl': 'http://en.wikipedia.org/',
                'kwargs': {
                    'random': '/wiki/Special:Random',
                    'search': '/wiki/Special:Search',
                    'advert': ' - Wikipedia, the free encyclopedia',
                    },
                },
            }

    pattern = Module._any
    terminate = False
    help = make_help(wikiconf)
    match_fmt = r'^\s*(?:%s)(?:\s+(.+?))?\s*$'

    citations_re = re.compile(r'\[.*?\]', re.DOTALL)
    parens_re = re.compile(r'\(.*?\)', re.DOTALL)
    whitespace_re = re.compile(r'[ \t\r\n]+')
    fix_punc_re = re.compile(r'\s+([,;:.])')
    sentence_re = re.compile(r'(.*?\.)\s+', re.DOTALL)
    summary_size = 400
    scripts_re = re.compile(r'<script [^>]+>.*?</script>', re.I | re.DOTALL)

    def init(self):
        self.wikis = {}
        for wiki, opts in self.wikiconf.iteritems():
            self.wikis[wiki] = {
                    'match_re': re.compile(self.match_fmt % '|'.join(opts['keys']), re.I),
                    'baseurl': opts['baseurl'],
                    'opts': opts['kwargs'],
                    }

    def response(self, nick, args, kwargs):
        message = args[0]
        for wiki, opts in self.wikis.iteritems():
            try:
                query = opts['match_re'].search(message).group(1)
                if query:
                    func, args = self.getsummary, (query,)
                else:
                    func, args = self.getrandom, ()
                res = func(*args, **dict(opts['opts'], baseurl=opts['baseurl']))
                if res:
                    return u'%s: %s' % (nick, res)
            except AttributeError:
                pass

    def getsummary(self, query, **kwargs):
        if not kwargs['search']:
            return u"i don't know how to search this wiki!"
        url = urljoin(kwargs['baseurl'], kwargs['search'])
        opts = {'search': query, 'go': 'Go'}
        return self._getsummary(url, opts=opts, **kwargs)

    def getrandom(self, **kwargs):
        if not kwargs['random']:
            return u"i don't know where random pages are on this wiki!"
        url = urljoin(kwargs['baseurl'], kwargs['random'])
        return self._getsummary(url, **kwargs)

    def _getsummary(self, url, opts=None, **kwargs):
        soup, title = self._getpage(url, opts, **kwargs)

        spam = soup.find('div', attrs={'id': 'siteNotice'})
        if spam is not None:
            spam.extract()

        # massage into plain text by concatenating paragraphs
        content = u' '.join(decode(p.renderContents(), 'utf-8') for p in soup.findAll('p'))

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

    def _getpage(self, url, opts=None, **kwargs):
        page = self.geturl(url, referer=kwargs['baseurl'], opts=opts)
        # HTMLParser doesn't handle this very well.. see:
        # http://www.crummy.com/software/BeautifulSoup/3.1-problems.html
        page = self.scripts_re.sub('', page)
        soup = BeautifulSoup(page)

        # get page title
        title = soup.title.string
        if kwargs['advert'] and kwargs['advert'] in title:
            title = title.replace(kwargs['advert'], '')

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
    def random_url(self):
        return urljoin(self.baseurl, self.random)
