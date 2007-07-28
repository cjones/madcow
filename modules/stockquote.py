#!/usr/bin/env python

"""
Get stock quote
"""

import sys
import re
import urllib
import os


class MatchObject(object):

    def __init__(self, config=None, ns='madcow', dir=None):
        self.enabled = True
        self.pattern = re.compile('^\s*(?:stocks?|quote)\s+([a-z0-9.-]+)', re.I)
        self.requireAddressing = True
        self.thread = True
        self.wrap = True
        self.help = 'quote <symbol> - get latest stock quote'

        self.company = re.compile('<td height="30" class="ygtb"><b>(.*?)</b>')
        self.lastTrade = re.compile('(Last Trade|Net Asset Value):</td><td class="yfnc_tabledata1"><big><b>(.*?)</b>')
        self.change = re.compile('Change:</td><td class="yfnc_tabledata1">(?:<img.*?alt="(.*?)">)? <b.*?>(.*?)</b>')

    def response(self, **kwargs):
        nick = kwargs['nick']
        args = kwargs['args']

        try:
            doc = urllib.urlopen('http://finance.yahoo.com/q?s=' + args[0]).read()
            company = self.company.search(doc).group(1)
            tag, lastTrade = self.lastTrade.search(doc).groups()
            change = self.change.search(doc)
            dir = change.group(1)
            change = change.group(2)
            if dir is not None:
                change = '%s %s' % (dir.lower(), change)
            else:
                change = None

            return '%s: %s - %s: %s, Change = %s' % (nick, company, tag, lastTrade, change)

        except Exception, e:
            print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
            return "%s: Couldn't look that up, guess the market crashed." % nick


if __name__ == '__main__':
    print MatchObject().response(nick=os.environ['USER'], args=[' '.join(sys.argv[1:])])
    sys.exit(0)
