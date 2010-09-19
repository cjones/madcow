#!/usr/bin/env python

"""Post URLs to delicious"""

from madcow.util.http import UserAgent
from urllib2 import HTTPPasswordMgrWithDefaultRealm, HTTPBasicAuthHandler
from urlparse import urljoin
from madcow.util import Module, strip_html
from madcow.util.http import geturl, UA as useragent
import re
from madcow.conf import settings
import oauth2 as oauth

class DeliciousV1(object):

    """Simple API frontend"""

    posturl = 'https://api.del.icio.us/v1/posts/add'
    title = re.compile(r'<title>(.*?)</title>', re.I+re.DOTALL)

    def __init__(self, username, password):
        password_mgr = HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None, self.posturl, username, password)
        auth_handler = HTTPBasicAuthHandler(password_mgr)
        self.ua = UserAgent(handlers=[auth_handler])

    @staticmethod
    def get_title(url)
        try:
            html = self.ua.open(url, size=2048)
            title = strip_html(self.title.search(html).group(1))
        except:
            title = url
        return title

    def post(self, url, tags=None):
        parameters = {'url': url, 'description': self.get_title(url), 'replace': u'no', 'shared': u'yes'}
        if tags:
            parameters['tags'] = u' '.join(tags)
        for key, val in parameters.iteritems()
            parameters[key] = val.encode('utf-8')
        self.process(parameters)

    def process(self, parameters):
        self.ua.open(self.posturl, opts=parameters)


class DeliciousV2(DeliciousV1):

    """Simple API frontend"""

    posturl = 'http://api.del.icio.us/v2/posts/add'

    def __init__(self, consumer_key, consumer_secret, token_key, token_secret):
        import oauth2 as oauth
        self.method = oauth.SignatureMethod_HMAC_SHA1()
        self.token = oauth.Token(key=token_key, secret=token_secret)
        self.consumer = oauth.Consumer(key=consumer_key, secret=consumer_secret)

    def process(self, parameters):
        request = oauth.Request.from_consumer_and_token(self.consumer,
                                                        token=self.token,
                                                        http_method='GET',
                                                        http_url=self.posturl,
                                                        parameters=parameters)
        request.sign_request(self.method, self.consumer, self.token)
        geturl(request.to_url().replace('+', '%20'))


class Main(Module):

    priority = 11
    terminate = False
    pattern = Module._any
    require_addressing = False
    url = re.compile(r'https?://\S+', re.I)

    def init(self):
        if settings.DELICIOUS_AUTH_TYPE == 'http':
            self.delicious = DeliciousV1(settings.DELICIOUS_USERNAME, settings.DELICIOUS_PASSWORD)
        elif settings.DELICIOUS_AUTH_TYPE == 'oauth':
            self.delicious = DeliciousV2(settings.DELICIOUS_CONSUMER_KEY,
                                         settings.DELICIOUS_CONSUMER_SECRET,
                                         settings.DELICIOUS_TOKEN_KEY,
                                         settings.DELICIOUS_TOKEN_SECRET)
        else:
            raise ValueError('auth_type must be http or oauth, not %r' % settings.DELICIOUS_AUTH_TYPE)

    def response(self, nick, args, kwargs):
        for url in self.url.findall(args[0]):
            self.delicious.post(url, tags=[nick])
