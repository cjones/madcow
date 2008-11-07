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

"""Return summary from WikiMedia projects"""

from utils import stripHTML
from useragent import geturl
from BeautifulSoup import BeautifulSoup
import re
from urlparse import urljoin

__version__ = u'0.1'
__author__ = u'cj_ <cjones@gruntle.org>'
__all__ = [u'Wiki']

class Wiki(object):

    """Return summary from WikiMedia projects"""

    # site-specific details, default is english wikipedia
    _base_url = u'http://en.wikipedia.org/'
    _random_path = u'/wiki/Special:Random'
    _search_path = u'/wiki/Special:Search'
    _advert = u' - Wikipedia, the free encyclopedia'
    _error = u'Search results'

    # size of response
    _summary_size = 400
    _sample_size = 32 * 1024

    # precompiled regex
    _citations = re.compile(r'\[.*?\]', re.DOTALL)
    _audio = re.compile(r'audiolink', re.I)
    _parens = re.compile(r'\(.*?\)', re.DOTALL)
    _whitespace = re.compile(r'[ \t\r\n]+')
    _sentence = re.compile(r'(.*?\.)\s+', re.DOTALL)
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
        content = stripHTML(content)                 # strip markup
        content = Wiki._citations.sub(u'', content)   # remove citations
        content = Wiki._parens.sub(u'', content)      # remove parentheticals
        content = Wiki._whitespace.sub(u' ', content) # compress whitespace
        content = Wiki._fix_punc.sub(r'\1', content) # fix punctuation
        content = content.strip()                    # strip whitespace

        # search error
        if title == self.error:
            return u'No results found for "%s"' % query

        # generate summary by adding as many sentences as possible before limit
        summary = u'%s -' % title
        for sentence in Wiki._sentence.findall(content):
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
        page = geturl(url, referer=self.base_url, opts=opts,
                      size=self.sample_size)

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
        for span in soup.findAll(u'span', attrs={u'class': Wiki._audio}):
            span.extract()

        return soup, title

