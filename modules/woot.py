#!/usr/bin/env python

"""get the current woot - author: Twid"""

from urlparse import urljoin
import sys
import re
from include import rssparser
from include.utils import Module, stripHTML

class Main(Module):
    pattern = re.compile('^\s*woot(?:\s+(\S+))?')
    require_addressing = True
    help = 'woot - get latest offer from woot.com'
    baseurl = 'http://woot.com'
    rssurl = urljoin(baseurl, '/Blog/Rss.aspx')
    max = 200

    def response(self, nick, args, **kwargs):
        try:
            feed = rssparser.parse(self.rssurl)

            # get latest entry and their homepage url
            title = feed['items'][0]['title'].split()
            offer = ' '.join(title[:-2])
            
            try:
                price = "$%.2f" % title[-1]
            except:
                price = ''

            longdescription = feed['items'][0]['description']
            page = feed['items'][0]['link']

            # strip out html
            longdescription = stripHTML(longdescription).strip()

            # these can get absurdly long
            if longdescription > self.max:
                longdescription = longdescription[:self.max-4] + ' ...'

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
    import os
    sys.exit(main())
