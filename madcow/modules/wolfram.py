"""query wolfram alpha api"""

from urlparse import ParseResult, urlunparse, urlparse
from urllib import urlencode, urlopen
import re

from lxml import etree

from madcow.util.text import decode
from madcow.conf import settings
from madcow.util import Module


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


class XMLParseError(ValueError):

    def __init__(self, xml, *args, **opts):
        super(XMLParseError, self).__init__(*args, **opts)
        self.xml = xml


api_uri = URI(scheme='http', netloc='api.wolframalpha.com', path='/v2/query')

def waquery(input, url=None, **opts):
    uri = api_uri if url is None else URI.from_url(url)
    opts['input'] = input
    tree = etree.parse(urlopen(uri._replace(query=urlencode(opts)).url))
    res = tree.xpath('/queryresult[@success="true"]/pod[@title="Result"]/*/plaintext/text()')
    if res:
        return decode(res[0]).strip()
    raise XMLParseError(etree.tostring(tree.getroot()), 'unexpected xml structure')


class Main(Module):

    pattern = re.compile(r'^\s*(?:wa|wolf(?:ram)?(?:\s*alpha)?)(?:\s+|\s*[:-]\s*)(.+?)\s*$', re.I)
    require_addressing = True
    help = u"<wa|wolf[ram][alpha]> <query> - query wolfram alpha database"
    error = u"no results, check logged xml response. NOTE: this module is very beta, so some things may not work. possibly many things. one might even venture to call this module 'alpha'"

    def init(self):
        self.appid = settings.WOLFRAM_API_APPID
        self.apiurl = settings.WOLFRAM_API_URL

    def response(self, nick, args, kwargs):
        if self.appid:
            try:
                res = waquery(args[0], appid=self.appid, url=self.apiurl)
            except XMLParseError, exc:
                self.log.warn(u'unhandled response for wolfram query. xml response:\n\n' + decode(exc.xml))
                return u'{}: {} [check logged xml response]'.format(nick, self.error)
            except (SystemExit, KeyboardInterrupt):
                raise
            except:
                from sys import exc_info
                return u'{}: internal exception: {}'.format(nick, decode(exc_info()[1]))
            else:
                return u'{}: {}'.format(nick, res)

