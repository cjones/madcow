#!/usr/bin/env python

"""Library to parse WikiPedia pages"""

import sys
from optparse import OptionParser
from BeautifulSoup import BeautifulSoup
import urllib, urllib2, cookielib
import re

__version__ = '0.1'
__author__ = 'Chris Jones <cjones@gruntle.org>'
__license__ = 'GPL'


class WikiParser(object):
    """Class that represents a WikiPedia page"""
    # constants
    AGENT = 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)'
    BASEURL = 'http://en.wikipedia.org/'
    ADVERT = ' - Wikipedia, the free encyclopedia'
    SUMMARY_SIZE = 400
    ERROR = 'No page with that title exists'
    SAMPLE_SIZE = 16 * 1024

    # precompiled regex's
    UTF8 = re.compile(r'[\x80-\xff]')
    MARKUP = re.compile(r'<.*?>', re.DOTALL)
    CITATIONS = re.compile(r'\[.*?\]', re.DOTALL)
    AUDIO = re.compile(r'audiolink', re.I)
    PARENS = re.compile(r'\(.*?\)', re.DOTALL)
    WHITESPACE = re.compile(r'[ \t\r\n]+')
    SENTENCE = re.compile(r'(.*?\.)\s+', re.DOTALL)

    def __init__(self, query):
        if isinstance(query, (list, tuple)):
            query = ' '.join(query)
        self.query = query

        # load page, mimic a browser to trick their anti-bot stuff
        cj = cookielib.CookieJar()
        ch = urllib2.HTTPCookieProcessor(cj)
        opener = urllib2.build_opener(ch)
        opener.addheaders = [('User-Agent', WikiParser.AGENT)]
        opts = {'search': self.query, 'go': 'Go'}
        url = WikiParser.BASEURL + 'wiki/Special:Search'
        req = urllib2.Request(url, urllib.urlencode(opts))
        req.add_header('Referer', WikiParser.BASEURL)
        res = opener.open(req)
        page = res.read(WikiParser.SAMPLE_SIZE)

        # remove high ascii from final page, this is going out to IRC
        page = WikiParser.UTF8.sub('', page)

        # create BeautifulSoup document tree
        soup = BeautifulSoup(page)

        # extract title
        self.title = soup.title.string.replace(WikiParser.ADVERT, '')

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
        for span in soup.findAll('span', attrs={'class': WikiParser.AUDIO}):
            span.extract()

        # massage into plain text by concatenating paragraphs
        content = []
        for para in soup.findAll('p'):
            content.append(str(para))
        content = ' '.join(content)

        # clean up rendered text
        content = WikiParser.MARKUP.sub('', content)      # strip HTML
        content = WikiParser.CITATIONS.sub('', content)   # remove citations
        content = WikiParser.PARENS.sub('', content)      # remove parenthesis
        content = WikiParser.WHITESPACE.sub(' ', content) # compress whitespace
        content = content.strip()                         # strip whitespace
        self.content = content

        # search error
        if self.title == 'Search' and WikiParser.ERROR in self.content:
            self.summary = 'No results found for "%s"' % self.query
            return

        # generate summary by adding as many sentences as possible before limit
        summary = '%s -' % self.title
        for sentence in WikiParser.SENTENCE.findall(self.content):
            if len(summary) + 1 + len(sentence) > WikiParser.SUMMARY_SIZE:
                break
            summary += ' %s' % sentence

        self.summary = summary

    def __str__(self):
        return '<WikiParser %s>' % self.query

    __repr__ = __str__


def main():
    op = OptionParser(version=__version__, usage='%prog [query]')
    opts, args = op.parse_args()

    wp = WikiParser(query=args)
    print wp.summary

    return 0

if __name__ == '__main__':
    sys.exit(main())
