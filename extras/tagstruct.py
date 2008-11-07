#!/usr/bin/env python

"""Take URL and return just markup structure"""

import sys
from optparse import OptionParser
from BeautifulSoup import BeautifulSoup
import urllib
import re

class HTMLParser:
    _tags = re.compile(r'<(/?\w+).*?>', re.DOTALL)
    _linebreaks = re.compile(r'[\r\n]+')
    _taglinks = re.compile(r'><')
    _tagdata = re.compile(r'>.*?<', re.DOTALL)
    _comments = re.compile(r'<!--.*?-->', re.DOTALL)

    def parse_url(self, url):
        data = urllib.urlopen(url)
        soup = BeautifulSoup(data)
        data = unicode(soup)
        data = self._comments.sub(u'', data)
        data = self._tags.sub(r'<\1>', data)
        data = self._linebreaks.sub(u'\n', data)
        data = self._tagdata.sub(u'><', data)
        data = self._taglinks.sub(u'>\n<', data)
        return data


def main():
    op = OptionParser()
    opts, args = op.parse_args()

    parser = HTMLParser()

    for url in args:
        data = parser.parse_url(url)
        print unicode(data)


    return 0

if __name__ == u'__main__':
    sys.exit(main())
