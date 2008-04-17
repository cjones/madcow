"""Return summary from WikiMedia projects"""

from utils import stripHTML, Base, UserAgent
from BeautifulSoup import BeautifulSoup
import re
from urlparse import urljoin

__version__ = '0.1'
__author__ = 'cj_ <cjones@gruntle.org>'
__license__ = 'GPL'
__all__ = ['Wiki']

class Wiki(Base):
    """Return summary from WikiMedia projects"""

    # site-specific details, default is english wikipedia
    _base_url = 'http://en.wikipedia.org/'
    _random_path = '/wiki/Special:Random'
    _search_path = '/wiki/Special:Search'
    _advert = ' - Wikipedia, the free encyclopedia'
    _error = 'Search results'

    # size of response
    _summary_size = 400
    _sample_size = 32 * 1024

    # precompiled regex
    _dash = '\xe2\x80\x94' # wikipedia people love their unicode :(
    _utf8 = re.compile(r'[\x80-\xff]')
    _citations = re.compile(r'\[.*?\]', re.DOTALL)
    _audio = re.compile(r'audiolink', re.I)
    _parens = re.compile(r'\(.*?\)', re.DOTALL)
    _whitespace = re.compile(r'[ \t\r\n]+')
    _sentence = re.compile(r'(.*?\.)\s+', re.DOTALL)
    _nbsp_entity = re.compile(r'&#160;')
    _fix_punc = re.compile(r'\s+([,;:.])')

    def __init__(self, base_url=_base_url, random_path=_random_path,
            search_path=_search_path, advert=_advert, error=_error,
            summary_size=_summary_size, sample_size=_sample_size):

        self.base_url = base_url
        self.random_path = random_path
        self.search_path = search_path
        self.advert = advert
        self.error = error
        self.summary_size = summary_size
        self.sample_size = sample_size
        self.ua = UserAgent()

    def get_summary(self, query):
        soup, title = self.get_soup(query)

        # check if this is a disambiguation page, if so construct special page
        # there isn't a consistent style guide, so we just try to do the
        # most common format (ordered list of links). if this fails, return
        # a friendly failure for now
        if soup.find('div', attrs={'id': 'disambig'}):
            try:
                summary = '%s (Disambiguation) - ' % title
                for link in soup.find('ul').findAll('a'):
                    title = str(link['title']).strip()
                    if len(summary) + len(title) + 2 > self.summary_size:
                        break
                    if not summary.endswith(' '):
                        summary += ', '
                    summary += title
            except:
                summary = 'Fancy, unsupported disambiguation page!'
            return summary

        # massage into plain text by concatenating paragraphs
        content = []
        for para in soup.findAll('p'):
            content.append(str(para))
        content = ' '.join(content)

        # clean up rendered text
        content = stripHTML(content)                 # strip markup
        content = Wiki._citations.sub('', content)   # remove citations
        content = Wiki._parens.sub('', content)      # remove parentheticals
        content = Wiki._whitespace.sub(' ', content) # compress whitespace
        content = Wiki._fix_punc.sub(r'\1', content) # fix punctuation
        content = content.strip()                    # strip whitespace

        # search error
        if title == self.error:
            return 'No results found for "%s"' % query

        # generate summary by adding as many sentences as possible before limit
        summary = '%s -' % title
        for sentence in Wiki._sentence.findall(content):
            if len(summary) + 1 + len(sentence) > self.summary_size:
                break
            summary += ' %s' % sentence
        return summary

    def get_soup(self, query):
        if isinstance(query, (list, tuple)):
            query = ' '.join(query)

        # load page
        if query == 'random':
            opts = {}
            url = urljoin(self.base_url, self.random_path)
        else:
            opts = {'search': query, 'go': 'Go'}
            url = urljoin(self.base_url, self.search_path)
        page = self.ua.fetch(url, referer=self.base_url, opts=opts,
                sample_size=self.sample_size)

        # remove high ascii since this is going to IRC
        page = Wiki._nbsp_entity.sub(' ', page)
        page = page.replace(Wiki._dash, ' -- ')
        page = Wiki._utf8.sub('', page)

        # create BeautifulSoup document tree
        soup = BeautifulSoup(page)

        # extract title minus WP advert
        title = soup.title.string.replace(self.advert, '')

        # remove all tabular data/sidebars
        for table in soup.findAll('table'):
            table.extract()

        # remove disambiguation links
        for dablink in soup.findAll('div', attrs={'class': 'dablink'}):
            dablink.extract()

        # remove latitude/longitude metadata for places
        for coord in soup.findAll('span', attrs={'id': 'coordinates'}):
            coord.extract()

        # strip non-english content wrappers
        for span in soup.findAll('span', attrs={'lang': True}):
            span.extract()

        # remove IPA pronounciation guidelines
        for span in soup.findAll('span', attrs={'class': 'IPA'}):
            span.extract()
        for link in soup.findAll('a', text='IPA'):
            link.extract()
        for span in soup.findAll('span', attrs={'class': Wiki._audio}):
            span.extract()

        return soup, title

