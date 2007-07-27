#!/usr/bin/env python

"""
Use Google as a calculator
"""

import sys
import re
import urllib
import urllib2
from include import utils
import os


class MatchObject(object):
    reConversionDetected = re.compile('More about (calculator|currency)')
    reConversionResult = re.compile('<h2 class=r>.*?<b>(.*?)<\/b><\/h2>')

    def __init__(self, config=None, ns='madcow', dir=None):
        self.enabled = True
        self.pattern = re.compile('^\s*calc\s+(.+)')
        self.requireAddressing = True
        self.thread = True
        self.wrap = False
        self.help = 'calc <expression> - pass expression to google calculator'

    def response(self, **kwargs):
        try:
            url = 'http://www.google.com/search?' + urllib.urlencode({
                'hl': 'en',
                'safe': 'off',
                'c2coff': 1,
                'btnG': 'Search',
                'q': ' '.join(kwargs['args']),
            })

            request = urllib2.Request(url)
            request.add_header('User-Agent', 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)')
            opener = urllib2.build_opener()
            doc = opener.open(request).read()

            if not MatchObject.reConversionDetected.search(doc):
                raise Exception

            response = MatchObject.reConversionResult.search(doc).group(1)
            response = utils.stripHTML(response)
            return '%s: %s' % (kwargs['nick'], response)

        except Exception, e:
            return '%s: No results, check your syntax at http://www.google.com/help/calculator.html' % kwargs['nick']


if __name__ == '__main__':
    print MatchObject().response(nick=os.environ['USER'], args=[' '.join(sys.argv[1:])])
    sys.exit(0)
