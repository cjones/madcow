#!/usr/bin/env python

"""Plugin to return summary from WikiPedia"""

from include.utils import Module
from include.wiki import Wiki
import re
import sys

class Main(Module):
    pattern = re.compile('^\s*(?:wp|wiki|wikipedia)\s+(.*?)\s*$', re.I)
    require_addressing = True
    help = 'wiki <term> - look up summary of term on wikipedia'

    def __init__(self, *args, **kwargs):
        self.wiki = Wiki()

    def response(self, nick, args, **kwargs):
        try:
            return self.wiki.get_summary(args)
        except Exception, e:
            print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
            return '%s: problem with query: %s' % (nick, e)


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
