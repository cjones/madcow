#!/usr/bin/env python

"""Plugin to return summary from ConservaPedia (lol)"""

from include.wiki import Wiki
import re

# these differ from wikipedia:
_baseurl = 'http://www.conservapedia.com/'
_random_path = '/Special:Random'
_advert = ' - Conservapedia'

class MatchObject(object):

    def __init__(self, *args, **kwargs):
        self.enabled = True
        self.pattern = re.compile('^\s*(?:cp)\s+(.*?)\s*$', re.I)
        self.requireAddressing = True
        self.thread = True
        self.wrap = False
        self.help = 'cp <term> - look up summary of term on conservapedia'
        self.wiki = Wiki(base_url=_baseurl, random_path=_random_path,
                advert=_advert)

    def response(self, **kwargs):
        try:
            return self.wiki.get_summary(kwargs['args'])
        except Exception, e:
            return '%s: problem with query: %s' % (kwargs['nick'], e)

if __name__ == '__main__':
    import os, sys
    print MatchObject().response(args=sys.argv[1:], nick=os.environ['USER'])
    sys.exit(0)
