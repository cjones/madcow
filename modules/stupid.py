#!/usr/bin/env python

"""Plugin to return summary from WikiPedia"""

import re
from include.BeautifulSoup import BeautifulSoup
import urllib, urllib2, cookielib
import re
from include import utils

# constants
AGENT = 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)'
BASEURL = 'http://stupidfilter.org/'
UTF8 = re.compile(r'[\x80-\xff]')

class MatchObject(object):

    def __init__(self, *args, **kwargs):
        self.enabled = True
        self.pattern = re.compile('^\s*(?:stupid)\s*$', re.I)
        self.requireAddressing = True
        self.thread = True
        self.wrap = False
        self.help = 'stupid - random stupid comment'

        # build opener to mimic browser
        cj = cookielib.CookieJar()
        ch = urllib2.HTTPCookieProcessor(cj)
        opener = urllib2.build_opener(ch)
        opener.addheaders = [('User-Agent', AGENT)]
        self.opener = opener

    def get_comment(self):
        # load page
        url = BASEURL + 'random.php'
        req = urllib2.Request(url)
        req.add_header('Referer', BASEURL)
        res = self.opener.open(req)
        page = res.read()

        # remove high ascii since this is going to IRC
        page = UTF8.sub('', page)

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

    def response(self, **kwargs):
        try:
            return self.get_comment()
        except Exception, e:
            return '%s: problem with query: %s' % (kwargs['nick'], e)

if __name__ == '__main__':
    import os, sys
    print MatchObject().response(nick=os.environ['USER'])
    sys.exit(0)
