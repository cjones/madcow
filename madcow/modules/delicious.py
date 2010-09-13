#!/usr/bin/env python

"""Post URLs to delicious"""

from madcow.util.http import UserAgent
from urllib2 import HTTPPasswordMgrWithDefaultRealm, HTTPBasicAuthHandler
from urlparse import urljoin
from madcow.util import Module, strip_html
import re
from madcow.conf import settings

class DeliciousV1(object):

    """Simple API frontend"""

    baseurl = u'https://api.del.icio.us/'
    posturl = urljoin(baseurl, u'/v1/posts/add')
    title = re.compile(r'<title>(.*?)</title>', re.I+re.DOTALL)

    def __init__(self, username, password):
        password_mgr = HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None, self.posturl, username, password)
        auth_handler = HTTPBasicAuthHandler(password_mgr)
        self.ua = UserAgent(handlers=[auth_handler])

    def post(self, url, tags):
        try:
            html = self.ua.open(url, size=2048)
            title = strip_html(self.title.search(html).group(1))
        except AttributeError:
            title = url
        opts = {u'url': url,
                u'description': title,
                u'tags': u' '.join(tags),
                u'replace': u'no',
                u'shared': u'yes'}
        self.ua.open(self.posturl, opts=opts)


class DeliciousV2(DeliciousV1):

    """Simple API frontend"""

    posturl = urljoin(baseurl, u'/v2/posts/add')

    def __init__(self, consumer_key, consumer_secret, token_key, token_secret):
        import oauth2 as oauth
        self.method = oauth.SignatureMethod_HMAC_SHA1()
        self.token = oauth.Token(key=token_key, secret=token_secret)
        self.consumer = oauth.Consumer(key=consumer_key, secret=consumer_secret)

    def post(self, url, tags):
        req = oauth.Request.from_consumer_and_token(
                self.consumer,
                token=self.token,
                http_method='POST',
                http_url=self.posturl,
                parameters=opts,
                )
        try:
            html = self.ua.open(url, size=2048)
            title = strip_html(self.title.search(html).group(1))
        except AttributeError:
            title = url
        opts = {u'url': url,
                u'description': title,
                u'tags': u' '.join(tags),
                u'replace': u'no',
                u'shared': u'yes'}
        self.ua.open(self.posturl, opts=opts)


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
            raise ValueError('auth_type must be http or oauth')

    def response(self, nick, args, kwargs):
        for url in self.url.findall(args[0]):
            self.delicious.post(url, tags=[nick])
