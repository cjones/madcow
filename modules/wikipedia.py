#!/usr/bin/env python

"""Plugin to return summary from WikiPedia"""

import re
from include.BeautifulSoup import BeautifulSoup
import urllib, urllib2, cookielib
import re
from include import utils

# constants
AGENT = 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)'
BASEURL = 'http://en.wikipedia.org/'
ADVERT = ' - Wikipedia, the free encyclopedia'
ERROR = 'For more information about searching Wikipedia'
SUMMARY_SIZE = 400
SAMPLE_SIZE = 32 * 1024

# precompiled regex
UTF8 = re.compile(r'[\x80-\xff]')
CITATIONS = re.compile(r'\[.*?\]', re.DOTALL)
AUDIO = re.compile(r'audiolink', re.I)
PARENS = re.compile(r'\(.*?\)', re.DOTALL)
WHITESPACE = re.compile(r'[ \t\r\n]+')
SENTENCE = re.compile(r'(.*?\.)\s+', re.DOTALL)
NBSP_ENTITY = re.compile(r'&#160;')
FIX_PUNC = re.compile(r'\s+([,;:.])')

class MatchObject(object):

    def __init__(self, *args, **kwargs):
        self.enabled = True
        self.pattern = re.compile('^\s*(?:wp|wiki|wikipedia)\s+(.*?)\s*$', re.I)
        self.requireAddressing = True
        self.thread = True
        self.wrap = False
        self.help = 'wiki <term> - look up summary of term on wikipedia'

        # build opener to mimic browser
        cj = cookielib.CookieJar()
        ch = urllib2.HTTPCookieProcessor(cj)
        opener = urllib2.build_opener(ch)
        opener.addheaders = [('User-Agent', AGENT)]
        self.opener = opener

    def get_summary(self, query):
        if isinstance(query, (list, tuple)):
            query = ' '.join(query)

        # load page
        opts = {'search': query, 'go': 'Go'}
        url = BASEURL + 'wiki/Special:Search'
        req = urllib2.Request(url, urllib.urlencode(opts))
        req.add_header('Referer', BASEURL)
        res = self.opener.open(req)
        page = res.read(SAMPLE_SIZE)

        # remove high ascii since this is going to IRC
        page = NBSP_ENTITY.sub(' ', page)
        page = UTF8.sub('', page)

        # create BeautifulSoup document tree
        soup = BeautifulSoup(page)

        # extract title minus WP advert
        title = soup.title.string.replace(ADVERT, '')

        # check if this is a disambiguation page, if so construct special page
        # there isn't a consistent style guide, so we just try to do the
        # most common format (ordered list of links). if this fails, return
        # a friendly failure for now
        if soup.find('div', attrs={'id': 'disambig'}):
            try:
                summary = '%s (Disambiguation) - ' % title
                for link in soup.find('ul').findAll('a'):
                    title = str(link['title']).strip()
                    if len(summary) + len(title) + 2 > SUMMARY_SIZE:
                        break
                    if not summary.endswith(' '):
                        summary += ', '
                    summary += title
            except:
                summary = 'Fancy, unsupported disambiguation page!'
            return summary

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
        for span in soup.findAll('span', attrs={'class': AUDIO}):
            span.extract()

        # massage into plain text by concatenating paragraphs
        content = []
        for para in soup.findAll('p'):
            content.append(str(para))
        content = ' '.join(content)

        # clean up rendered text
        content = utils.stripHTML(content)     # strip markup and entities
        content = CITATIONS.sub('', content)   # remove citations
        content = PARENS.sub('', content)      # remove parentheticals
        content = WHITESPACE.sub(' ', content) # compress whitespace
        content = FIX_PUNC.sub(r'\1', content) # fix punctuation
        content = content.strip()              # strip lead/traili whitespace

        # search error
        if title == 'Search results' and ERROR in content:
            return 'No results found for "%s"' % query

        # generate summary by adding as many sentences as possible before limit
        summary = '%s -' % title
        for sentence in SENTENCE.findall(content):
            if len(summary) + 1 + len(sentence) > SUMMARY_SIZE:
                break
            summary += ' %s' % sentence
        return summary

    def response(self, **kwargs):
        try:
            return self.get_summary(kwargs['args'])
        except Exception, e:
            return '%s: problem with query: %s' % (kwargs['nick'], e)

if __name__ == '__main__':
    import os, sys
    print MatchObject().response(args=sys.argv[1:], nick=os.environ['USER'])
    sys.exit(0)
