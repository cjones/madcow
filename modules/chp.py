#!/usr/bin/env python

"""Get traffic info from CHP website (bay area only)"""

import re
from include.utils import Module, stripHTML
from include.useragent import geturl
import logging as log

class Main(Module):
    pattern = re.compile('^\s*chp\s+(.+)', re.I)
    require_addressing = True
    help = 'chp <highway> - look for CHP reports for highway, such as 101'
    url = 'http://cad.chp.ca.gov/sa_list.asp?centerin=GGCC&style=l'
    incidents = re.compile('<tr>(.*?)</tr>', re.DOTALL)
    data = re.compile('<td class="T".*?>(.*?)</td>')
    clean = re.compile('[^0-9a-z ]', re.I)

    def response(self, nick, args, kwargs):
        query = args[0]
        try:
            check = self.clean.sub('', query)
            check = re.compile(check, re.I)

            results = []
            doc = geturl(self.url)
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
            log.warn('error in %s: %s' % (self.__module__, e))
            log.exception(e)
            return '%s: I failed to perform that lookup' % nick


if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)
