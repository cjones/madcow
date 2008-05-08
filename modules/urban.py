#!/usr/bin/env python

"""Look up a definition in the Urban Dictionary"""

import sys
import re
import SOAPpy
import os
from include.utils import Base

class Main(Base):
    enabled = True
    pattern = re.compile('^\s*urban\s+(.+)')
    require_addressing = True


    help = 'urban <phrase> - look up a word/phrase on urban dictionary'
    key = 'a979884b386f8b7ea781754892f08d12'

    def __init__(self, madcow=None):
        self.server = SOAPpy.SOAPProxy("http://api.urbandictionary.com/soap")

    def response(self, nick, args, **kwargs):
        try:
            words = args[0].split()
            if words[-1].isdigit():
                i = int(words[-1])
                term = ' '.join(words[:-1])
            else:
                i = 1
                term = ' '.join(words)


            items = self.server.lookup(self.key, term)

            max = len(items)
            if max == 0:
                return "%s: So obscure even urban dictionary doesn't know what it means" % nick

            if i > max:
                return '%s: CRITICAL BUFFER OVERFLOW ERROR' % nick

            item = items[i - 1]
            response = '%s: [%s/%s] %s - Example: %s' % (nick, i, max, item.definition, item.example)
            return response.encode("utf-8")

        except Exception, e:
            print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
            return "%s: Serious problems: %s" % (nick, e)


def main():
    try:
        main = Main()
        args = main.pattern.search(' '.join(sys.argv[1:])).groups()
        print main.response(nick=os.environ['USER'], args=args)
    except Exception, e:
        print 'no match: %s' % e

if __name__ == '__main__':
    sys.exit(main())
