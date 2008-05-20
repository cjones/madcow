#!/usr/bin/env python

"""Module stub"""

from include.useragent import geturl
from include.utils import Module
import sys
import re

class Main(Module):
    pattern = re.compile(r'^\s*keyword\s+(\S+)\s*', re.I)
    require_addressing = True
    help = 'help message for this addon'

    def __init__(self, madcow=None):
        self.madcow = madcow

    def response(self, nick, args, **kwargs):
        try:
            return 'not impemented'
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
