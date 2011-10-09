"""Tools to mimic browser capabilities for scraping tasks"""

import htmlentitydefs
import collections
import cookielib
import urlparse
import urllib2
import urllib
import gzip
import re

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

try:
    from PIL import Image
except ImportError:
    Image = None

from gruntle.memebot.exceptions import *
from gruntle.memebot.utils import text, inflate

__all__ = ['Browser', 'decode_entities', 'render_node']

DEFAULT_MAX_REDIRECTS = 10

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

# some gloriously naive regular expressions for stripping html, quick & dirty
html_tag_re = re.compile(r'<.*?>', re.DOTALL)  # <-- horrible
lang_tag_re = re.compile(r'<(script|style)[^>]*>.*?</\1>', re.IGNORECASE | re.DOTALL)
comment_re = re.compile(r'<!--.*?-->', re.DOTALL)
whitespace_re = re.compile(r'\s+')  # for packing whitespace
entity_dec_re = re.compile(r'(&#(\d+);)')  # &#32;
entity_hex_re = re.compile(r'^(&#x([0-9a-fA-F]+);)')  # &#x3D;
entity_name_re = re.compile(r'(&(%s);)' % '|'.join(map(re.escape, htmlentitydefs.name2codepoint)))  # &amp;
meta_refresh_re = re.compile(r'^refresh$', re.IGNORECASE)
site_names_re = re.compile(r'(?:^|\.)(([^.]+)\.[^.]+)$')

class Response(collections.namedtuple('Response', 'code msg url real_url data_type main_type sub_type data complete raw')):

    @property
    def is_valid(self):
        return self.code == 200

    @property
    def redirected(self):
        return self.url != self.real_url

    @property
    def content_type(self):
        return '%s/%s' % (self.main_type, self.sub_type)

    @property
    def meta_redirect(self):
        if self.data_type == 'soup':
            with trapped:
                for param in self.data.head.find('meta', {'http-equiv': meta_refresh_re})['content'].split(';'):
                    if param.startswith(u'url='):
                        return param[4:]

    def __str__(self):
        return text.encode(', '.join(text.format('%s=%r', key, getattr(self, key, None))
                                     for key in self._fields if key not in ('data', 'raw')))

    def __repr__(self):
        return text.format('<%s: %s>', type(self).__name__, self.__str__())


class Browser(object):

    """Represents a configured browser"""

    def __init__(self,
                 handlers=None,
                 headers=None,
                 user_agent='urllib2',
                 support_cookies=True,
                 support_gzip=True,
                 add_accept_headers=True,
                 keepalive=True,
                 timeout=None,
                 max_redirects=None,
                 max_read=None):

        if handlers is None:
            handlers = []
        if headers is None:
            headers = []
        if max_redirects is None:
            max_redirects = DEFAULT_MAX_REDIRECTS
        if max_read is None:
            max_read = -1

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
        self.max_redirects = max_redirects
        self.max_read = max_read
        self.timeout = timeout
        self.opener = urllib2.build_opener(*handlers)
        self.opener.addheaders = self.headers = headers

        if etree is None:
            self.xml_parser = None
        else:
            self.xml_parser = etree.XMLParser(encoding=text.get_encoding(), ns_clean=True,
                                              recover=True, remove_blank_text=True, strip_cdata=False)

    def open(self, url, data=None, referer=None, follow_meta_redirect=False):
        """Opens the requested URL"""
        followed = set()
        orig_url = url
        response = None
        while True:
            try:
                with TrapErrors():
                    response = self._open(url, data, referer)
            except TrapError, exc:
                # exception on first attempt, just raise it, we got nothing useful
                if response is None:
                    reraise(*exc.args)
                # otherwise, this was probably an error from meta redirect, we can keep the earlier response
                #import traceback
                #traceback.print_exception(*exc.args)
                break
            if not follow_meta_redirect:
                break
            redirect = response.meta_redirect
            if redirect is None or redirect in followed:
                break
            followed.add(redirect)
            if len(followed) > self.max_redirects:
                break
            url = redirect
        return response

    def _open(self, url, data=None, referer=None):
        request = urllib2.Request(text.encode(url), data)
        if referer is not None:
            request.add_header('Referer', referer)
        try:
            response = self.opener.open(request, timeout=self.timeout)
        except urllib2.HTTPError, exc:
            response = exc
        data = response.read(self.max_read)
        read = len(data)

        length = response.headers.get('content-length')
        if length is not None:
            length = int(length)
            complete = read >= int(length)
        else:
            complete = (self.max_read == -1) or (read < self.max_read)

        content_encoding = response.headers.get('content-encoding')
        if content_encoding == 'gzip':
            data = gzip.GzipFile(fileobj=stringio.StringIO(data), mode='r').read()
        elif content_encoding == 'deflate':
            data = inflate(data)

        raw = data

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
            except TrapError:
                data_type = 'broken_xml'
        else:
            data_type = 'unknown'

        if response.headers.maintype == 'image' and Image is not None:
            try:
                with TrapErrors():
                    fileobj = stringio.StringIO(data)
                    data = Image.open(fileobj)
                    data.load()
                    data_type = 'image'
            except TrapError:
                data_type = 'broken_image'

        return Response(code=response.code, msg=response.msg, url=url, real_url=response.url, data_type=data_type,
                        main_type=response.headers.maintype, sub_type=response.headers.subtype, data=data,
                        complete=complete, raw=raw)


def decode_entities(html):
    """Convert HTML entity-encoded characters back to bytes"""
    for a in ((x, unichr(int(v))) for x, v in entity_dec_re.findall(html)):
        html = html.replace(*a)
    for a in ((x, unichr(htmlentitydefs.name2codepoint[name])) for x, name in entity_name_re.findall(html)):
        html = html.replace(*a)
    for a in ((x, unichr(int(v, 16))) for x, v in entity_hex_re.findall(html)):
        html = html.replace(*a)
    return html


def render_node(node):
    """Try to turn a soup node into something resembling plain text"""
    if isinstance(node, (str, unicode)):
        html = node
    else:
        html = node.renderContents()
    html = text.decode(html)
    html = html_tag_re.sub(u' ', html)
    html = decode_entities(html)
    html = html.replace(u'\u00a0', ' ')
    html = whitespace_re.sub(u' ', html)
    html = html.strip()
    return html


def prettify_node(node):
    """Try to turn a soup node into something resembling readable html"""
    if isinstance(node, (str, unicode)):
        html = node
    else:
        html = node.prettify()
    html = text.decode(html)
    html = lang_tag_re.sub(u' ', html)
    html = comment_re.sub(u' ', html)
    html = html.strip()
    lines = html.splitlines()
    lines = (line.rstrip() for line in lines)
    lines = (line for line in lines if line)
    html = u'\n'.join(lines) + u'\n'
    return text.encode(html)


def strip_site_name(title, url):
    """Try to strip site names from html titles"""
    try:
        host = urlparse.urlparse(url).netloc.lower()
        pattern = '\s*[|-]\s*(?:%s)\s*$' % '|'.join(re.escape(name) for name in site_names_re.search(host).groups())
        return re.sub(pattern, '', title, flags=re.IGNORECASE)
    except StandardError:
        return title
