#!/usr/bin/env python

"""Module stub"""

import sys
import re
import os
from include.utils import Base

class Main(Base):
    """This object is autoloaded by the bot"""
    pattern = re.compile(r'^\s*keyword\s+(\S+)', re.I)
    enabled = True
    require_addressing = True


    help = None

    def __init__(self, madcow=None):
        """Module-specific initializations go here"""
        self.madcow = madcow

    def response(self, nick, args, **kwargs):
        """This function should return a response to the query or None."""

        try:
            pass
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
