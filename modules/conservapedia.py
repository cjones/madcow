#!/usr/bin/env python

"""Plugin to return summary from ConservaPedia (lol)"""

from include.wiki import Wiki
import re
from include.utils import Base
import sys
import os

# these differ from wikipedia:
_baseurl = 'http://www.conservapedia.com/'
_random_path = '/Special:Random'
_advert = ' - Conservapedia'

class Main(Base):
    enabled = True
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
            return '%s: problem with query: %s' % (nick, e)


def main():
    try:
        main = Main()
        args = main.pattern.search(' '.join(sys.argv[1:])).groups()
        print main.response(nick=os.environ['USER'], args=args)
    except Exception, e:
        print 'no match: %s' % e

if __name__ == '__main__':
    sys.exit(main())
