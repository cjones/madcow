#!/usr/bin/env python

"""Scrape BBC news"""

import sys
import re
from include import rssparser
from include.utils import Base, stripHTML
import os
import urllib
from urlparse import urljoin

class Main(Base):
    enabled = True
    pattern = re.compile('^\s*bbcnews(?:\s+(.+))?', re.I)
    require_addressing = True


    help = 'bbcnews <string> - Searches the BBC News Website'

    _error = 'Looks like the BBC aren\'t co-operating today.'
    _api_url = 'http://newsapi.bbc.co.uk/'
    _search_url = urljoin(_api_url, '/feeds/search/news/')
    _rss_url = 'http://newsrss.bbc.co.uk/'
    _world_url = urljoin(_rss_url, '/rss/newsonline_uk_edition/world/rss.xml')

    def response(self, **kwargs):
        nick = kwargs['nick']
        query = kwargs['args'][0]

        try:
            if len(query) == 0 or query == 'headline':
                url = self._world_url
            else:
                url = self._search_url + urllib.quote(query)
                            
            feed = rssparser.parse(url)
            item = feed['items'][0]
            url = item['link']
            title = stripHTML(item['title'])
            sum = stripHTML(item['description'])
            return '\n'.join((url, title, sum))
            
        except Exception, e:
            print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
            return '%s: %s' % (nick, self._error)


def main():
    try:
        main = Main()
        args = main.pattern.search(' '.join(sys.argv[1:])).groups()
        print main.response(nick=os.environ['USER'], args=args)
    except Exception, e:
        print 'no match: %s' % e

if __name__ == '__main__':
    sys.exit(main())
