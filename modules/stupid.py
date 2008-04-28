#!/usr/bin/env python

"""Stupid quotes"""

import re
from include.BeautifulSoup import BeautifulSoup
from include.utils import Base, UserAgent, stripHTML
from urlparse import urljoin
import os
import sys

class Main(Base):
    enabled = True
    pattern = re.compile('^\s*(?:stupid)\s*$', re.I)
    require_addressing = True


    help = 'stupid - random stupid comment'
    base_url = 'http://stupidfilter.org/'
    url = urljoin(base_url, '/random.php')
    utf8 = re.compile(r'[\x80-\xff]')

    def __init__(self, madcow=None):
        self.ua = UserAgent()

    def get_comment(self):
        page = self.ua.fetch(self.url)

        # remove high ascii since this is going to IRC
        page = self.utf8.sub('', page)

        # create BeautifulSoup document tree
        soup = BeautifulSoup(page)
        table = soup.find('table')
        rows = table.findAll('tr')
        row = rows[1]
        cells = row.findAll('td')
        source = cells[1].string
        comment = cells[2].string
        author = cells[3].string
        return '<%s@%s> %s' % (author, source, comment)

    def response(self, **kwargs):
        try:
            return self.get_comment()
        except Exception, e:
            return '%s: problem with query: %s' % (kwargs['nick'], e)


def main():
    try:
        main = Main()
        args = main.pattern.search(' '.join(sys.argv[1:])).groups()
        print main.response(nick=os.environ['USER'], args=args)
    except Exception, e:
        print 'no match: %s' % e

if __name__ == '__main__':
    sys.exit(main())
