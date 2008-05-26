#!/usr/bin/env python

"""Stupid quotes"""

import re
from include.BeautifulSoup import BeautifulSoup
from include.utils import Module, stripHTML
from include.useragent import geturl
from urlparse import urljoin
import logging as log

class Main(Module):
    pattern = re.compile('^\s*(?:stupid)\s*$', re.I)
    require_addressing = True
    help = 'stupid - random stupid comment'
    base_url = 'http://stupidfilter.org/'
    url = urljoin(base_url, '/random.php')
    utf8 = re.compile(r'[\x80-\xff]')

    def get_comment(self):
        page = geturl(self.url)

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

    def response(self, nick, args, **kwargs):
        try:
            return self.get_comment()
        except Exception, e:
            log.warn('error in %s: %s' % (self.__module__, e))
            log.exception(e)
            return '%s: make your own stupid quotes' % nick


if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)
