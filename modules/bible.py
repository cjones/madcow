#!/usr/bin/env python

"""JESUS!"""

import re
from include.utils import Module, stripHTML
from include.useragent import geturl
from urlparse import urljoin
import logging as log

class Main(Module):
    pattern = re.compile('^\s*bible\s+(\S+\s+\d+:[0-9-]+)', re.I)
    require_addressing = True
    help = 'bible <book> <chp>:<verse>[-<verse>] - spam jesus stuff'
    baseurl = 'http://www.biblegateway.com/'
    passage = urljoin(baseurl, '/passage/')
    verse = re.compile('<div class="result-text-style-normal">(.*?)</div>',
            re.DOTALL)
    footnotes = re.compile('<strong>Footnotes:</strong>.*$', re.DOTALL)
    junk_html = re.compile(r'<(h4|h5|span|sup|strong|ol|a).*?</\1>', re.I)
    max = 800

    def response(self, nick, args, **kwargs):
        query = args[0]

        try:
            doc = geturl(self.passage, opts={'search': query, 'version': 31})
            response = self.verse.search(doc).group(1)
            response = self.footnotes.sub('', response)
            response = self.junk_html.sub('', response)
            response = stripHTML(response)
            response = response.strip()
            return response[:self.max]
        except Exception, e:
            log.warn('error in %s: %s' % (self.__module__, e))
            log.exception(e)
            return "%s: God didn't like that." % nick


if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)
