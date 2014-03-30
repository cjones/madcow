"""query wolfram alpha api"""

from urlparse import ParseResult, urlunparse, urlparse
from urllib import urlencode, urlopen

import sys
import re

from lxml import etree

from madcow.util.text import decode
from madcow.conf import settings
from madcow.util import Module


uesc_re = re.compile(ur'\\:([0-9a-fA-F]{4})', re.U)
xrespath = '/queryresult[@success="true"]/pod[@title="Result"]/*/plaintext/text()'


class URI(ParseResult):

    @classmethod
    def from_url(cls, url):
        return cls._make(urlparse(url))

    def __new__(cls, scheme='', netloc='', path='', params='', query='', fragment=''):
        return super(URI, cls).__new__(cls, scheme, netloc, path, params, query, fragment)

    def to_url(self):
        return urlunparse(self)

    url = property(to_url)

    def __str__(self):
        return self.url

api_uri = URI(scheme='http', netloc='api.wolframalpha.com', path='/v2/query')


class XMLParseError(ValueError):

    def __init__(self, xml, *args, **opts):
        super(XMLParseError, self).__init__(*args, **opts)
        self.xml = xml


def waquery(input, url=None, **opts):
    tree = etree.parse(urlopen((URI.from_url(url) if url else api_uri)._replace(
        query=urlencode(dict(opts, input=input))).url))
    res = tree.xpath(xrespath)
    if not res:
        raise XMLParseError(etree.tostring(tree.getroot()), 'unexpected xml structure')
    res = decode(res[0])
    for match in uesc_re.finditer(res):
        res = res.replace(match.group(0), unichr(int(match.group(1), 16)), 1)
    return res.strip()


class Main(Module):

    require_addressing = True
    pattern = re.compile(r'^\s*(?:wa|wolf(?:ram)?(?:\s*alpha)?)(?:\s+|\s*[:-]\s*)(.+?)\s*$', re.I)
    help = u'<wa|wolf[ram][alpha]> <query> - query wolfram alpha database'
    error = u'no results, check logs for exact xml response'

    def init(self):
        self.appid = settings.WOLFRAM_API_APPID
        self.apiurl = settings.WOLFRAM_API_URL

    def response(self, nick, args, kwargs):
        if self.appid:
            try:
                res = waquery(args[0], appid=self.appid, url=self.apiurl)
            except XMLParseError, exc:
                self.log.warn(u'unhandled response for wolfram query. xml response:')
                self.log.warn(repr(exc.xml))
                return u'{}: {}'.format(nick, self.error)
            except (SystemExit, KeyboardInterrupt):
                raise
            except:
                return u'{}: internal exception: {}'.format(nick, decode(sys.exc_value))
            else:
                return u'{}: {}'.format(nick, res)
