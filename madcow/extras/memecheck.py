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

dbinfo = dict(user=u'memebot', passwd=u'memebot', db=u'memebot')
chksql = (u'SELECT url.posted, author.name FROM url, author WHERE url.author_i'
          u'd = author.id AND url.clean = %s ORDER BY url.posted ASC;')

def clean_url(url):
    netloc = query = fragment = u''
    i = url.find(u':')
    scheme = url[:i].lower()
    url = url[i+1:]
    if url[:2] == u'//':
        delim = len(url)
        for c in u'/?#':
            wdelim = url.find(c, 2)
            if wdelim >= 0:
                delim = min(delim, wdelim)
        netloc, url = url[2:delim], url[delim:]
    if u'#' in url:
        try:
            url, fragment = get_frag.search(url).groups()
        except:
            pass
    if u'?' in url:
        url, query = url.split(u'?', 1)
    netloc = netloc.lower()
    if netloc.startswith(u'www.') and len(netloc) > 4:
        netloc = netloc[4:]
    if url == u'':
        url = u'/'
    try:
        query = query.split(u'&')
        query = [part.split(u'=') for part in query]
        query = [[x, y] for x, y in query if len(y)]
        query = [u'='.join([x, y]) for x, y in query]
        query = sorted(query)
        query = u'&'.join(query)
    except:
        query = u''
    fragment = u''
    return urlparse.urlunsplit([scheme, netloc, url, query, fragment])


def memecheck(url):
    url = clean_url(url)
    db = MySQLdb.connect(**dbinfo)
    cursor = db.cursor()
    cursor.execute(chksql, args=(url,))
    results = cursor.fetchall()
    if not results:
        return u'<font color="green">NEW MEME</font>'
    time, author = results[0]
    return u'<font color="red">OLD MEME: First posted by %s on %s</font>' % (
            author, time.ctime())

def main():
    sys.stdout.write(u'Content-Type: text/html\r\n\r\n')
    try:
        url = cgi.FieldStorage()[u'url'].value
        print url + u'<hr/>'
        print memecheck(url)
    except:
        print u'missing url?'

    return 0

if __name__ == u'__main__':
    sys.exit(main())
