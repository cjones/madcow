#!/usr/bin/env python

"""Plugin to return summary from ConservaPedia (lol)"""

import sys
from include.wiki import Wiki
from include.utils import Module
import re

# these differ from wikipedia:
_baseurl = 'http://www.conservapedia.com/'
_random_path = '/Special:Random'
_advert = ' - Conservapedia'

class Main(Module):
    pattern = re.compile('^\s*(?:cp)\s+(.*?)\s*$', re.I)
    require_addressing = True
    help = 'cp <term> - look up summary of term on conservapedia'

    def __init__(self, madcow=None):
        self.wiki = Wiki(base_url=_baseurl, random_path=_random_path,
                advert=_advert)

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
