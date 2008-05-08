#!/usr/bin/env python

"""Interface for getting really stupid IRC quotes"""

import sys
import re
import random
from include.utils import Base, UserAgent, stripHTML
import os

class Bash(Base):
    random = 'http://www.bash.org/?random'
    bynum = 'http://www.bash.org/?num'
    search = 'http://www.bash.org/?search=query&show=100'
    entries = re.compile('<p class="qt">(.*?)</p>', re.DOTALL)


class QDB(Base):
    random = 'http://qdb.us/random'
    bynum = 'http://qdb.us/num'
    search = 'http://qdb.us/?search=query&limit=100&approved=1'
    entries = re.compile('<td[^>]+><p>(.*?)</p>', re.DOTALL)


class XKCD(Base):
    random = 'http://www.chiliahedron.com/xkcdb/?random'
    bynum = 'http://www.chiliahedron.com/xkcdb/?num'
    search = 'http://www.chiliahedron.com/xkcdb/?search=query&show=100'
    entries = re.compile('<div class="quote_output">\s*(.*?)</div>', re.DOTALL)


class Limerick(Base):
    random = 'http://www.limerickdb.com/?random'
    bynum = 'http://www.limerickdb.com/?num'
    search = 'http://www.limerickdb.com/?search=query&number=100'
    entries = re.compile('<div class="quote_output">\s*(.*?)\s*</div>', re.DOTALL)


class Main(Base):
    enabled = True
    pattern = re.compile('^\s*(bash|qdb|xkcdb|limerick)(?:\s+(\S+))?', re.I)
    require_addressing = True


    help = '<bash|qdb|xkcdb|limerick> [#|query] - get stupid IRC quotes'

    sources = {
        'bash': Bash(),
        'qdb': QDB(),
        'xkcdb': XKCD(),
        'limerick': Limerick(),
    }
    _error = 'Having some issues, make some stupid quotes yourself'

    def __init__(self, madcow=None):
        self.madcow = madcow
        self.ua = UserAgent()

    def response(self, nick, args, **kwargs):
        try:
            source = self.sources[args[0]]

            try:
                query = args[1]
            except:
                query = None

            try:
                num = int(query)
                query = None
            except:
                num = None

            if num:
                url = source.bynum.replace('num', str(num))
            elif query:
                url = source.search.replace('query', query)
            else:
                url = source.random

            doc = self.ua.fetch(url)
            entries = source.entries.findall(doc)

            if query:
                entries = [entry for entry in entries if query in entry]

            if len(entries) > 1:
                entry = random.choice(entries)
            else:
                entry = entries[0]

            return stripHTML(entry)

        except Exception, e:
            print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
            return '%s: %s' % (nick, self._error)


def main():
    try:
        main = Main()
        args = main.pattern.search(' '.join(sys.argv[1:])).groups()
        print main.response(nick=os.environ['USER'], args=args)
    except Exception, e:
        print 'no match: %s' % e

if __name__ == '__main__':
    sys.exit(main())
