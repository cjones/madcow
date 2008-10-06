#!/usr/bin/env python

import sys
import MySQLdb
import urlparse
import cgi

"""Quick, nasty cgi hack to check whether a meme is safe to post or not

the bookmarklet to invoke this:

(change the url from gruntle.org/memecheck/check to the path to this script)

javascript:(%20function()%20{%20var%20url%20=%20'http://gruntle.org/memecheck/check?url='%20+%20escape(window.location.href);%20var%20params%20=%20'width=588,height=156,toolbar=0,status=1,location=0,scrollbars=0,menubar=0,resizable=0';%20w%20=%20open(url,%20'w',%20params);%20setTimeout('w.focus()',%200);%20})();
"""

dbinfo = dict(user='memebot', passwd='memebot', db='memebot')
chksql = ('SELECT url.posted, author.name FROM url, author WHERE url.author_i'
          'd = author.id AND url.clean = %s ORDER BY url.posted ASC;')

def clean_url(url):
    netloc = query = fragment = ''
    i = url.find(':')
    scheme = url[:i].lower()
    url = url[i+1:]
    if url[:2] == '//':
        delim = len(url)
        for c in '/?#':
            wdelim = url.find(c, 2)
            if wdelim >= 0:
                delim = min(delim, wdelim)
        netloc, url = url[2:delim], url[delim:]
    if '#' in url:
        try:
            url, fragment = get_frag.search(url).groups()
        except:
            pass
    if '?' in url:
        url, query = url.split('?', 1)
    netloc = netloc.lower()
    if netloc.startswith('www.') and len(netloc) > 4:
        netloc = netloc[4:]
    if url == '':
        url = '/'
    try:
        query = query.split('&')
        query = [part.split('=') for part in query]
        query = [[x, y] for x, y in query if len(y)]
        query = ['='.join([x, y]) for x, y in query]
        query = sorted(query)
        query = '&'.join(query)
    except:
        query = ''
    fragment = ''
    return urlparse.urlunsplit([scheme, netloc, url, query, fragment])


def memecheck(url):
    url = clean_url(url)
    db = MySQLdb.connect(**dbinfo)
    cursor = db.cursor()
    cursor.execute(chksql, args=(url,))
    results = cursor.fetchall()
    if not results:
        return '<font color="green">NEW MEME</font>'
    time, author = results[0]
    return '<font color="red">OLD MEME: First posted by %s on %s</font>' % (
            author, time.ctime())

def main():
    sys.stdout.write('Content-Type: text/html\r\n\r\n')
    try:
        url = cgi.FieldStorage()['url'].value
        print url + '<hr/>'
        print memecheck(url)
    except:
        print 'missing url?'

    return 0

if __name__ == '__main__':
    sys.exit(main())
