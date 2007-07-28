#!/usr/bin/env python

"""
Look up drink mixing ingredients
"""

import sys
import re
import urllib
from include import utils
import os


class MatchObject(object):

    def __init__(self, config=None, ns='madcow', dir=None):
        self.enabled = True
        self.pattern = re.compile('^\s*drinks?\s+(.+)')
        self.requireAddressing = True
        self.thread = True
        self.wrap = True
        self.help = 'drinks <drink name> - look up mixing instructions'

        self.baseURL = 'http://www.webtender.com'
        self.drink = re.compile('<A HREF="(/db/drink/\d+)">')

        self.title = re.compile('<H1>(.*?)<HR></H1>')
        self.ingredients = re.compile('<LI>(.*?CLASS=ingr.+)')
        self.instructions = re.compile('<H3>Mixing instructions:</H3>.*?<P>(.*?)</P>', re.DOTALL)

    def response(self, **kwargs):
        nick = kwargs['nick']
        args = kwargs['args']
        url = self.baseURL + '/cgi-bin/search?' + urllib.urlencode({
            'verbose': 'on',
            'name': args[0],
        })

        try:
            doc = urllib.urlopen(url).read()
            drink = self.drink.search(doc).group(1)
            doc = urllib.urlopen(self.baseURL + drink).read()

            title = self.title.search(doc).group(1)
            ingredients = self.ingredients.findall(doc)
            instructions = self.instructions.search(doc).group(1)

            response = '%s: %s - %s - %s' % (nick, title, ', '.join(ingredients), instructions)
            response = utils.stripHTML(response)

            return response

        except Exception, e:
            print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
            return "%s: Something ungood happened looking that up, sry" % nick


if __name__ == '__main__':
    print MatchObject().response(nick=os.environ['USER'], args=[' '.join(sys.argv[1:])])
    sys.exit(0)
