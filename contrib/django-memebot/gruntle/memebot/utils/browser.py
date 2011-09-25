"""Tools to mimic browser capabilities for scraping tasks"""

import collections
import cookielib
import urllib2
import urllib
import gzip

try:
    import cStringIO as stringio
except ImportError:
    import StringIO as stringio

try:
    from BeautifulSoup import BeautifulSoup
except ImportError:
    BeautifulSoup = None

try:
    from lxml import etree
except ImportError:
    etree = None

from gruntle.memebot.utils import TrapError, TrapErrors, text

# some user agents to choose from, for convenience
PRESET_USER_AGENTS = {'ie6': 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)',
                      'ie7': 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0)',
                      'ie8': 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1)',
                      'google': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
                      'msn': 'msnbot/1.1 (+http://search.msn.com/msnbot.htm)',
                      'yahoo': 'Mozilla/5.0 (compatible; Yahoo! Slurp; http://help.yahoo.com/help/us/ysearch/slurp)',
                      'iphone': 'Mozilla/5.0 (iPhone; U; CPU iPhone OS 3_0 like Mac OS X; en-us) '
                                'AppleWebKit/528.18 (KHTML, like Gecko) Version/4.0 Mobile/7A341 Safari/528.16',
                      'firefox': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.7; rv:6.0.2) Gecko/20100101 Firefox/6.0.2',
                      'chrome': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_1) '
                                'AppleWebKit/535.2 (KHTML, like Gecko) Chrome/15.0.874.24 Safari/535.2',
                      'safari': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_1) '
                                'AppleWebKit/534.48.3 (KHTML, like Gecko) Version/5.1 Safari/534.48.3',
                      'w3m': 'w3m/0.5.3',
                      'wget': 'Wget/1.12 (linux-gnu)',
                      'urllib': 'Python-urllib/1.17',
                      'urllib2': 'Python-urllib/2.7'}

class Response(collections.namedtuple('Response', 'code msg orig_url real_url data_type main_type sub_type data')):

    @property
    def is_valid(self):
        return self.code == 200

    @property
    def redirected(self):
        return self.orig_url != self.real_url

    @property
    def mime_type(self):
        return '%s/%s' % (self.main_type, self.sub_type)


class Browser(object):

    """Represents a configured browser"""

    def __init__(self, handlers=None, headers=None, user_agent='urllib2', support_cookies=True,
                 support_gzip=True, add_accept_headers=True, keepalive=True, timeout=None):

        if handlers is None:
            handlers = []
        if headers is None:
            headers = []

        # add cookie processor to handlers if we want cookie support
        if support_cookies:
            self.cookie_jar = cookielib.CookieJar()
            handlers.append(urllib2.HTTPCookieProcessor(self.cookie_jar))
        else:
            self.cookie_jar = None

        # optional headers to appear more like a real browser
        if user_agent is not None:
            try:
                user_agent = PRESET_USER_AGENTS[user_agent]
            except KeyError:
                pass
            headers.append(('User-Agent', user_agent))
        if support_gzip:
            headers.append(('Accept-Encoding', 'gzip, deflate'))
        if add_accept_headers:
            headers.extend((('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
                            ('Accept-Language', 'en-us,en;q=0.5'),
                            ('Accept-Charset', 'ISO-8859-1,utf-8;q=0.7,*;q=0.7')))

        if keepalive:
            headers.append(('Connection', 'keep-alive'))

        # build the opener
        self.timeout = timeout
        self.opener = urllib2.build_opener(*handlers)
        self.opener.addheaders = self.headers = headers

        if etree is None:
            self.xml_parser = None
        else:
            self.xml_parser = etree.XMLParser(encoding=text.get_encoding(), ns_clean=True,
                                              recover=True, remove_blank_text=True, strip_cdata=False)

    def open(self, url, data=None, referer=None, max_read=None):
        """Opens the requested URL"""
        request = urllib2.Request(url, data)
        if referer is not None:
            request.add_header('Referer', referer)
        try:
            response = self.opener.open(request, timeout=self.timeout)
        except urllib2.HTTPError, exc:
            response = exc
        if max_read is None:
            max_read = -1
        data = response.read(max_read)
        if response.headers.get('content-encoding') == 'gzip':
            data = gzip.GzipFile(fileobj=stringio.StringIO(data), mode='r').read()
        if response.headers.maintype == 'text':
            data = text.decode(data, response.headers.getparam('charset'))
            data_type = 'text'
        if response.headers.subtype == 'html' and BeautifulSoup is not None:
            try:
                with TrapErrors():
                    data = BeautifulSoup(data)
                    data_type = 'soup'
            except TrapError:
                data_type = 'broken_html'
        elif response.headers.subtype == 'xml' and etree is not None:
            try:
                with TrapErrors():
                    data = etree.ElementTree(etree.fromstring(data, parser=self.xml_parser))
                    data_type = 'etree'
            except TrapError, exc:
                data_type = 'broken_xml'
        else:
            data_type = 'unknown'

        return Response(code=response.code, msg=response.msg, orig_url=url, real_url=response.url, data_type=data_type,
                        main_type=response.headers.maintype, sub_type=response.headers.subtype, data=data)
