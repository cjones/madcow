#!/usr/bin/env python

"""
JESUS!
"""

import sys
import re
import urllib
from include import utils
import os


class MatchObject(object):

    def __init__(self, config=None, ns='madcow', dir=None):
        self.enabled = True
        self.pattern = re.compile('^\s*bible\s+(\S+\s+\d+:[0-9-]+)')
        self.requireAddressing = True
        self.thread = True
        self.wrap = True
        self.help = 'bible <book> <chp>:<verse>[-<verse>] - spam jesus stuff'

        self.baseURL = 'http://www.biblegateway.com/passage/'
        self.verse = re.compile('<div class="result-text-style-normal">(.*?)</div>', re.DOTALL)
        self.footnotes = re.compile('<strong>Footnotes:</strong>.*$', re.DOTALL)
        self.junkHTML = re.compile(r'<(h4|h5|span|sup|strong|ol|a).*?</\1>', re.I)
        self.max = 800

    def response(self, **kwargs):
        nick = kwargs['nick']
        args = kwargs['args']

        try:
            url = self.baseURL + '?' + urllib.urlencode(
                    {    'search'    : args[0],
                        'version'    : 31,    }
                    )
            doc = urllib.urlopen(url).read()

            response = self.verse.search(doc).group(1)
            response = self.footnotes.sub('', response)
            response = self.junkHTML.sub('', response)
            response = utils.stripHTML(response)
            response = response.strip()

            return response[:self.max]

        except Exception, e:
            print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
            return "%s: God didn't like that." % nick


if __name__ == '__main__':
    print MatchObject().response(nick=os.environ['USER'], args=[' '.join(sys.argv[1:])])
    sys.exit(0)
