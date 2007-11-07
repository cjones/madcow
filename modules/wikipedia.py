#!/usr/bin/env python

"""Get summary from WikiPedia"""

import sys
import re
import os
import cookielib
import urllib, urllib2
from include import utils


class WikiPedia(object):
    """WikiPedia parser object"""
    BASEURL = 'http://en.wikipedia.org/'
    ADVERT = 'Wikipedia, the free encyclopedia'
    parse_title = re.compile('<title>(.*?) - ' + ADVERT + '</title>', re.I)
    content = re.compile(r'<!-- start content -->(.*?)<!-- end content -->',
            re.I + re.DOTALL)
    linefeed = re.compile(r'[\r\n]+')
    whitespace = re.compile(r'\s+')
    sentence = re.compile(r'(.*?\.)\s+', re.DOTALL)
    dablink = re.compile(r'<div[^>]+class="dablink".*?<\/div>', re.I+re.DOTALL)
    table = re.compile(r'<table.*?<\/table>', re.I+re.DOTALL)
    SUMMARY_SIZE = 400
    ERROR = 'No page with that title exists'

    def __init__(self, query, opener):
        if isinstance(query, list):
            query = ' '.join(query)
        self.query = query
        self.opener = opener
        self.title = 'unknown'
        self.summary = 'blah blah [citation needed]'
        self.loadPage()

    def loadPage(self):
        opts = {'search': self.query, 'go': 'Go'}
        url = WikiPedia.BASEURL + 'wiki/Special:Search'
        req = urllib2.Request(url, urllib.urlencode(opts))
        req.add_header('Referer', WikiPedia.BASEURL)
        data = self.opener.open(req).read()
        try:
            self.title = WikiPedia.parse_title.search(data).group(1)
            content = WikiPedia.content.search(data).group(1)
            content = WikiPedia.dablink.sub(' ', content)
            content = WikiPedia.table.sub(' ', content)
            content = utils.stripHTML(content)
            content = WikiPedia.linefeed.sub(' ', content)
            content = WikiPedia.whitespace.sub(' ', content)
        except:
            pass

        lines = WikiPedia.sentence.findall(content)
        self.summary = '%s -' % self.title
        for line in lines:
            line = line.strip()
            if len(self.summary) + 1 + len(line) > WikiPedia.SUMMARY_SIZE:
                break
            self.summary += ' %s' % line

        self.content = content

        if self.title == 'Search' and WikiPedia.ERROR in self.summary:
            raise Exception, "couldn't find a page for %s" % repr(self.query)


class MatchObject(object):
    """This object is autoloaded by the bot"""
    AGENT = 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)'

    def __init__(self, config=None, ns='madcow', dir='..'):
        self.ns = ns
        self.dir = dir
        self.config = config
        self.enabled = True
        self.pattern = re.compile('^\s*(?:wp|wiki|wikipedia)\s+(.*?)\s*$', re.I)
        self.requireAddressing = True
        self.thread = True
        self.wrap = False
        self.help = 'wiki <term> - look up summary of term on wikipedia'

        # build agent
        cj = cookielib.CookieJar()
        ch = urllib2.HTTPCookieProcessor(cj)
        opener = urllib2.build_opener(ch)
        opener.addheaders = [('User-Agent', MatchObject.AGENT)]
        self.opener = opener

    def response(self, **kwargs):
        """This function should return a response to the query or None. """

        nick = kwargs['nick']
        args = kwargs['args']

        try:
            wp = WikiPedia(query=args[0], opener=self.opener)
            return wp.summary

        except Exception, e:
            return '%s: problem with query: %s' % (nick, e)


if __name__ == '__main__':
    mo = MatchObject()
    res = mo.response(nick=os.environ['USER'], args=[' '.join(sys.argv[1:])])
    print res
    sys.exit(0)
