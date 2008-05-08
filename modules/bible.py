#!/usr/bin/env python

"""JESUS! """

import sys
import re
from include.utils import Base, UserAgent, stripHTML
import os

class Main(Base):
    enabled = True
    pattern = re.compile('^\s*bible\s+(\S+\s+\d+:[0-9-]+)', re.I)
    require_addressing = True


    help = 'bible <book> <chp>:<verse>[-<verse>] - spam jesus stuff'

    baseURL = 'http://www.biblegateway.com/passage/'
    verse = re.compile('<div class="result-text-style-normal">(.*?)</div>', re.DOTALL)
    footnotes = re.compile('<strong>Footnotes:</strong>.*$', re.DOTALL)
    junkHTML = re.compile(r'<(h4|h5|span|sup|strong|ol|a).*?</\1>', re.I)
    max = 800

    def __init__(self, madcow=None):
        self.madcow = madcow
        self.ua = UserAgent()

    def response(self, nick, args, **kwargs):
        query = args[0]

        try:
            opts = {'search'    : query, 'version': 31}
            doc = self.ua.fetch(self.baseURL, opts=opts)

            response = self.verse.search(doc).group(1)
            response = self.footnotes.sub('', response)
            response = self.junkHTML.sub('', response)
            response = stripHTML(response)
            response = response.strip()

            return response[:self.max]

        except Exception, e:
            print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
            return "%s: God didn't like that." % nick


def main():
    try:
        main = Main()
        args = main.pattern.search(' '.join(sys.argv[1:])).groups()
        print main.response(nick=os.environ['USER'], args=args)
    except Exception, e:
        print 'no match: %s' % e

if __name__ == '__main__':
    sys.exit(main())
