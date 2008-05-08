#!/usr/bin/env python

"""Look up drink mixing ingredients"""

import sys
import re
from include.utils import Base, UserAgent, stripHTML
from urlparse import urljoin
import os

class Main(Base):
    enabled = True
    pattern = re.compile('^\s*drinks?\s+(.+)', re.I)
    require_addressing = True


    help = 'drinks <drink name> - look up mixing instructions'

    baseURL = 'http://www.webtender.com/'
    search = urljoin(baseURL, '/cgi-bin/search')
    drink = re.compile('<A HREF="(/db/drink/\d+)">')
    title = re.compile('<H1>(.*?)<HR></H1>')
    ingredients = re.compile('<LI>(.*?CLASS=ingr.+)')
    instructions = re.compile('<H3>Mixing instructions:</H3>.*?<P>(.*?)</P>', re.DOTALL)

    def __init__(self, madcow=None):
        self.ua = UserAgent()

    def response(self, nick, args, **kwargs):
        query = args[0]

        try:
            opts = {'verbose': 'on', 'name': query}
            doc = self.ua.fetch(self.search, opts=opts)
            drink = self.drink.search(doc).group(1)
            url = urljoin(self.baseURL, drink)
            doc = self.ua.fetch(url)
            title = self.title.search(doc).group(1)
            ingredients = self.ingredients.findall(doc)
            instructions = self.instructions.search(doc).group(1)

            response = '%s: %s - %s - %s' % (nick, title,
                    ', '.join(ingredients), instructions)
            response = stripHTML(response)

            return response

        except Exception, e:
            print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
            return "%s: Something ungood happened looking that up, sry" % nick


def main():
    try:
        main = Main()
        args = main.pattern.search(' '.join(sys.argv[1:])).groups()
        print main.response(nick=os.environ['USER'], args=args)
    except Exception, e:
        print 'no match: %s' % e

if __name__ == '__main__':
    sys.exit(main())
