#!/usr/bin/env python

"""Get traffic info from CHP website (bay area only)"""

import sys
import re
from include.utils import Base, UserAgent, stripHTML
import os

class Main(Base):
    enabled = True
    pattern = re.compile('^\s*chp\s+(.+)', re.I)
    require_addressing = True


    help = 'chp <highway> - look for CHP reports for highway, such as 101'

    url = 'http://cad.chp.ca.gov/sa_list.asp?centerin=GGCC&style=l'
    incidents = re.compile('<tr>(.*?)</tr>', re.DOTALL)
    data = re.compile('<td class="T".*?>(.*?)</td>')
    clean = re.compile('[^0-9a-z ]', re.I)

    def __init__(self, madcow=None):
        self.ua = UserAgent()

    def response(self, **kwargs):
        nick = kwargs['nick']
        query = kwargs['args'][0]
        try:
            check = self.clean.sub('', query)
            check = re.compile(check, re.I)

            results = []
            doc = self.ua.fetch(self.url)
            for i in self.incidents.findall(doc):
                data = [stripHTML(c) for c in self.data.findall(i)][1:]
                if len(data) != 4:
                    continue
                if check.search(data[2]):
                    results.append('=> %s: %s - %s - %s' % (data[0], data[1],
                        data[2], data[3]))

            if len(results) > 0:
                return '\n'.join(results)
            else:
                return '%s: No incidents found' % nick

        except Exception, e:
            print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
            return '%s: I failed to perform that lookup' % nick


def main():
    try:
        main = Main()
        args = main.pattern.search(' '.join(sys.argv[1:])).groups()
        print main.response(nick=os.environ['USER'], args=args)
    except Exception, e:
        print 'no match: %s' % e

if __name__ == '__main__':
    sys.exit(main())
