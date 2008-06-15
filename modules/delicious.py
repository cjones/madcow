#!/usr/bin/env python

"""Post URLs to delicious"""

from include.useragent import UserAgent
from urllib2 import HTTPPasswordMgrWithDefaultRealm, HTTPBasicAuthHandler
from urlparse import urljoin
from include.utils import Module, stripHTML
import re
import logging as log

class Delicious:
    """Simple API frontend"""

    baseurl = 'https://api.del.icio.us/'
    posturl = urljoin(baseurl, '/v1/posts/add')
    title = re.compile(r'<title>(.*?)</title>', re.I+re.DOTALL)

    def __init__(self, username, password):
        password_mgr = HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None, self.posturl, username, password)
        auth_handler = HTTPBasicAuthHandler(password_mgr)
        self.ua = UserAgent(handlers=[auth_handler])

    def post(self, url, tags):
        try:
            html = self.ua.openurl(url, size=2048)
            title = stripHTML(self.title.search(html).group(1))
        except:
            title = url
        opts = {
            'url': url,
            'description': title,
            'tags': ' '.join(tags),
            'replace': 'no',
            'shared': 'yes',
        }
        self.ua.openurl(self.posturl, opts=opts)


class Main(Module):
    priority = 11
    terminate = False
    pattern = Module._any
    require_addressing = False
    url = re.compile(r'https?://\S+', re.I)

    def __init__(self, madcow=None):
        try:
            username = madcow.config.delicious.username
            password = madcow.config.delicious.password
        except:
            username = ''
            password = ''
        if not username or not password:
            self.enabled = False
            return
        self.delicious = Delicious(username, password)

    def response(self, nick, args, kwargs):
        try:
            for url in self.url.findall(args[0]):
                self.delicious.post(url, tags=['madcow', nick])
        except Exception, e:
            log.warn('error in %s: %s' % (self.__module__, e))
            log.exception(e)

