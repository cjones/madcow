"""Closely mimic a browser (kinda..)"""

from gzip import GzipFile

import collections
import encoding
import urlparse
import httplib
import urllib2
import urllib
import socket
import sys
import re

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from BeautifulSoup import BeautifulSoup

from text import encode, decode, get_encoding


# just some random real user agent so we don't appear as a bot..
AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.9; rv:46.0) Gecko/20100101 Firefox/46.0'
VERSION = sys.version_info[0] * 10 + sys.version_info[1]
UA = None


class odict(collections.MutableMapping):

    def __init__(self, *args, **kwargs):
        self._dict = {}
        self._order = []
        for key, val in dict(*args, **kwargs).iteritems():
            self[key] = val

    def __delitem__(self, key):
        del self._dict[key]
        self._order.remove(key)

    def __getitem__(self, key):
        return self._dict[key]

    def __iter__(self):
        return iter(self._order)

    def __len__(self):
        return len(self._order)

    def __setitem__(self, key, val):
        if key not in self._dict:
            self._order.append(key)
        self._dict[key] = val

    def __str__(self):
        return repr(self._dict)


class UserAgent(object):

    def __init__(self, handlers=None, cookies=True, agent=AGENT, debug=False, logger=None):
        if handlers is None:
            handlers = []
        if cookies:
            handlers.append(urllib2.HTTPCookieProcessor)
        self.opener = urllib2.build_opener(*handlers)
        if agent:
            self.opener.addheaders = [(u'User-Agent', agent)]
        self.debug = debug

    def open(self, url, opts=None, data=None, referer=None, size=-1,
             add_headers=None, logger=None, **kwargs):
        """Open URL and return unicode content"""
        realurl = buildurl(opts=opts, **dict(urlparse.urlparse(url)._asdict(), **kwargs))
        if logger is not None:
            logger.debug('open url: {}'.format(realurl))
        request = urllib2.Request(realurl, data)
        if referer:
            request.add_header(u'Referer', referer)
        if add_headers:
            for item in add_headers.items():
                request.add_header(*item)
        response = self.opener.open(request)
        data = response.read(size)
        import google
        headers = None if isinstance(response, google.Response) else response.headers
        if headers and headers.get('content-encoding') == 'gzip':
            data = GzipFile(fileobj=StringIO(data)).read()
        return encoding.convert(data, headers)

    @staticmethod
    def settimeout(timeout):
        """Monkey-patch socket timeout if older urllib2"""
        def connect(self):
            try:
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.sock.settimeout(timeout)
                self.sock.connect((self.host, self.port))
            except socket.error, error:
                if self.sock:
                    self.sock.close()
                self.sock = None
                raise error

        httplib.HTTPConnection.connect = connect


def getua():
    """Returns global user agent instance"""
    global UA
    if UA is None:
        UA = UserAgent()
    return UA


def setup(handlers=None, cookies=True, agent=AGENT, timeout=None):
    """Create global user agent instance"""
    global UA
    UserAgent.settimeout(timeout)
    UA = UserAgent(handlers, cookies, agent)


def geturl(*args, **kwargs):
    return getua().open(*args, **kwargs)

geturl.__doc__ = UserAgent.open.__doc__


def getsoup(*args, **kwargs):
    """geturl wrapper to return soup minus scripts/styles"""
    return BeautifulSoup(geturl(*args, **kwargs))


def is_sequence(obj):
    t = type(obj)
    return (issubclass(t, (collections.Iterable, collections.Iterator))
            and not issubclass(t, basestring))


def expandquery(query):
    if query is None:
        query = []
    elif isinstance(query, basestring):
        query = urlparse.parse_qsl(query)
    elif isinstance(query, collections.Mapping):
        query = list(query.iteritems())
    return [(encode(key), map(encode, val if is_sequence(val) else [val]))
            for key, val in query]


def mergeopts(*opts):
    merged = odict()
    for opts in map(expandquery, opts):
        for key, vals in opts:
            merged.setdefault(key, []).extend(vals)
    return expandquery(merged)


def buildurl(scheme=None, netloc=None, host=None, port=None, path=None,
             query=None, params=None, fragment=None, opts=None, **kwargs):
    if netloc is not None:
        host, _, port = netloc.partition(':')
    if not host:
        scheme, host = 'file', 'localhost'
    elif port:
        port = int(port)
    if not scheme:
        scheme = 'https' if port == 443 else 'http'
    if (scheme == 'file' or
            (scheme == 'http' and port == 80) or
            (scheme == 'https' and port == 443)):
        port = None
    return urlparse.urlunparse(urlparse.urlparse('')._replace(
        scheme=scheme, netloc='{}:{}'.format(host, port) if port else host,
        path=path, query=urllib.urlencode(mergeopts(query, opts, kwargs), doseq=1),
        params=params, fragment=fragment))


def getopt(query, opt):
    for key, vals in expandquery(query):
        if key == opt and vals:
            return vals[0]


def geturlopt(url, opt):
    uri = urlparse.urlparse(url)
    return getopt(uri.query, opt)

