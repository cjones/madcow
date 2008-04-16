#!/usr/bin/env python

"""Plugin to return random quote from WikiQuotes"""

from include.wiki import Wiki
import re

_base_url = 'http://en.wikiquote.org/'
_advert = ' - Wikiquote'
_summary_size = Wiki._summary_size
_sample_size = Wiki._sample_size

class MatchObject(object):

    def __init__(self, *args, **kwargs):
        self.enabled = True
        self.pattern = re.compile(r'^\s*wikiquote\s*$', re.I)
        self.requireAddressing = True
        self.thread = True
        self.wrap = False
        self.help = 'wikiquote - get random quote from wikiquotes'
        self.wiki = Wiki(base_url=_base_url, advert=_advert,
                summary_size=_summary_size, sample_size=_sample_size)

    def get_random_quote(self):
        return 'not implemented'

    def response(self, **kwargs):
        try:
            return self.get_random_quote()
        except Exception, e:
            return '%s: problem with query: %s' % (kwargs['nick'], e)

if __name__ == '__main__':
    import os, sys
    print MatchObject().response(args=sys.argv[1:], nick=os.environ['USER'])
    sys.exit(0)
