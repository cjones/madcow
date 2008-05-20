#!/usr/bin/env python

"""Use Google as a calculator"""

import re
from include.utils import Module, stripHTML
from include.useragent import geturl
from urlparse import urljoin
import sys

class Main(Module):
    pattern = re.compile('^\s*calc\s+(.+)', re.I)
    require_addressing = True
    help = 'calc <expression> - pass expression to google calculator'
    reConversionDetected = re.compile('More about (calculator|currency)')
    reConversionResult = re.compile('<h2 class=r>.*?<b>(.*?)<\/b><\/h2>')
    _base_url = 'http://www.google.com/'
    _search_url = urljoin(_base_url, '/search')

    def response(self, nick, args, **kwargs):
        try:
            opts = {
                'hl': 'en',
                'safe': 'off',
                'c2coff': 1,
                'btnG': 'Search',
                'q': ' '.join(args),
            }

            doc = geturl(self._search_url, opts=opts)

            if not self.reConversionDetected.search(doc):
                raise Exception, 'no conversion detected'

            response = self.reConversionResult.search(doc).group(1)
            response = stripHTML(response)
            return '%s: %s' % (nick, response)

        except Exception, e:
            print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
            return '%s: No results (bad syntax?)' % nick


def main():
    try:
        main = Main()
        args = main.pattern.search(' '.join(sys.argv[1:])).groups()
        print main.response(nick=os.environ['USER'], args=args)
    except Exception, e:
        print 'no match: %s' % e

if __name__ == '__main__':
    import os
    sys.exit(main())
