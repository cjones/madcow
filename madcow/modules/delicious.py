#!/usr/bin/env python

"""Post URLs to delicious"""

from madcow.util.http import UserAgent
from urllib2 import HTTPPasswordMgrWithDefaultRealm, HTTPBasicAuthHandler
from urlparse import urljoin
from madcow.util import Module, stripHTML
import re
from madcow.conf import settings

class Delicious(object):

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
            title = stripHTML(self.title.search(html).group(1))
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

    def __init__(self, madcow=None):
        try:
            username = DELICIOUS_USERNAME
            password = DELICIOUS_PASSWORD
        except:
            username = u''
            password = u''
        if not username or not password:
            self.enabled = False
            return
        self.delicious = Delicious(username, password)

    def response(self, nick, args, kwargs):
        for url in self.url.findall(args[0]):
            self.delicious.post(url, tags=[nick])
