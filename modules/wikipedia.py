#!/usr/bin/env python

"""Plugin to return summary from WikiPedia"""

from include.wiki import Wiki
import re

class MatchObject(object):

    def __init__(self, *args, **kwargs):
        self.enabled = True
        self.pattern = re.compile('^\s*(?:wp|wiki|wikipedia)\s+(.*?)\s*$', re.I)
        self.requireAddressing = True
        self.thread = True
        self.wrap = False
        self.help = 'wiki <term> - look up summary of term on wikipedia'
        self.wiki = Wiki()

    def response(self, **kwargs):
        try:
            return self.wiki.get_summary(kwargs['args'])
        except Exception, e:
            return '%s: problem with query: %s' % (kwargs['nick'], e)

if __name__ == '__main__':
    import os, sys
    print MatchObject().response(args=sys.argv[1:], nick=os.environ['USER'])
    sys.exit(0)
