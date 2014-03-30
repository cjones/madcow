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

    @property
    def url(self):
        return urlunparse(self)


class XPaths:

    result = '/queryresult[@success="true" and @error="false"]/pod[@id="Result"]/*/plaintext/text()'
    suggests = '/queryresult[@success="false" and @error="false"]/didyoumeans/didyoumean/text()'
    error = '/queryresult[@success="false" and @error="true"]'


class Main(Module):

    require_addressing = True
    pattern = re.compile(r'^\s*(?:wa|wolf(?:ram)?(?:\s*alpha)?)(?:\s+|\s*[:-]\s*)(.+?)\s*$', re.I)
    help = u'<wa|wolf[ram][alpha]> <query> - query wolfram alpha database'
    default_api_uri = URI(scheme='http', netloc='api.wolframalpha.com', path='/v2/query')
    unicode_esc_re = re.compile(ur'\\:([0-9a-fA-F]{4})', re.U)

    def init(self):
        self.appid = settings.WOLFRAM_API_APPID
        self.apiurl = settings.WOLFRAM_API_URL

    def response(self, nick, args, kwargs):
        if self.appid:
            try:
                res = self.wolfram_query(args[0], appid=self.appid, url=self.apiurl)
            except (SystemExit, KeyboardInterrupt):
                raise
            except:
                self.log.exception('uncaught exception querying wolfram alpha')
                res = u'unexpected exception during query, file a bug'
            return u'{}: {}'.format(nick, res)

    def log_xml(self, tree):
        self.log.warn('WolframAlpha Response XML:')
        self.log.warn(decode(etree.tostring(tree.getroot())))

    def wolfram_query(self, input, url=None, **opts):
        api_uri = URI.from_url(url) if url else self.default_api_uri
        query_string = urlencode(dict(opts, input=input))
        request_url = api_uri._replace(query=query_string).url
        response = urlopen(request_url)
        tree = etree.parse(response)
        if tree.xpath(XPaths.error):
            self.log_xml(tree)
            result = 'Error response from the server, check logs.'
        else:
            result = tree.xpath(XPaths.result)
            if result:
                result = result[0]
            else:
                result = 'No results.'
                suggests = ', '.join(tree.xpath(XPaths.suggests)).strip()
                if suggests:
                    result += ' Did you mean: ' + suggests
                else:
                    self.log_xml(tree)
                    result += ' This may be in error, check logs for XML response.'
        result = decode(result)
        for match in self.unicode_esc_re.finditer(result):
            result = result.replace(match.group(0), unichr(int(match.group(1), 16)), 1)
        return result.strip()

