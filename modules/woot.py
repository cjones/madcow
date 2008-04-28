#!/usr/bin/env python

"""get the current woot - author: Twid"""

from urlparse import urljoin
import sys
import re
from include import rssparser
from include.utils import Base, stripHTML
import os
import string

class Main(Base):
    enabled = True
    pattern = re.compile('^\s*woot(?:\s+(\S+))?')
    require_addressing = True


    help = 'woot - get latest offer from woot.com'

    baseURL = 'http://woot.com'
    max = 200

    def response(self, **kwargs):
        nick = kwargs['nick']

        try:
            url = urljoin(self.baseURL, '/Blog/Rss.aspx')
            feed = rssparser.parse(url)

            # get latest entry and their homepage url
            title = string.split(feed['items'][0]['title'])
            offer = string.join(title[:-2])
            
            try:
                price = "$%s" % string.atof(title[-1])
            except:
                price = ''

            longdescription = feed['items'][0]['description']
            page = feed['items'][0]['link']

            # strip out html
            longdescription = string.lstrip(stripHTML(longdescription))

            # these can get absurdly long
            longdescription = longdescription[:self.max] + ' ...'

            return '%s: %s\n[%s]\n%s' % (offer, price, page, longdescription)

        except Exception, e:
            print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
            return "%s: Couldn't load the page woot returned D:" % nick


def main():
    try:
        main = Main()
        args = main.pattern.search(' '.join(sys.argv[1:])).groups()
        print main.response(nick=os.environ['USER'], args=args)
    except Exception, e:
        print 'no match: %s' % e

if __name__ == '__main__':
    sys.exit(main())
