#!/usr/bin/env python

"""
Get traffic info from CHP website (bay area only)
"""

import sys
import re
import urllib
from include import utils
import os


class MatchObject(object):

    def __init__(self, config=None, ns='madcow', dir=None):
        self.enabled = True
        self.pattern = re.compile('^\s*chp\s+(.+)', re.I)
        self.requireAddressing = True
        self.thread = True
        self.wrap = False
        self.help = 'chp <highway> - look for CHP reports for highway, such as 101'

        self.url = 'http://cad.chp.ca.gov/sa_list.asp?centerin=GGCC&style=l'
        self.incidents = re.compile('<tr>(.*?)</tr>', re.DOTALL)
        self.data = re.compile('<td class="T".*?>(.*?)</td>')
        self.clean = re.compile('[^0-9a-z ]', re.I)

    def response(self, **kwargs):
        nick = kwargs['nick']
        args = kwargs['args']
        try:
            check = self.clean.sub('', args[0])
            check = re.compile(check, re.I)

            results = []
            for i in self.incidents.findall(urllib.urlopen(self.url).read()):
                data = [utils.stripHTML(c) for c in self.data.findall(i)][1:]
                if len(data) != 4: continue
                if check.search(data[2]):
                    results.append('=> %s: %s - %s - %s' % (data[0], data[1], data[2], data[3]))

            if len(results) > 0:
                return '\n'.join(results)
            else:
                return '%s: No incidents found' % nick

        except Exception, e:
            print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
            return '%s: I failed to perform that lookup' % nick


if __name__ == '__main__':
    print MatchObject().response(nick=os.environ['USER'], args=[' '.join(sys.argv[1:])])
    sys.exit(0)
