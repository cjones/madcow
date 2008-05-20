#!/usr/bin/env python

"""Post URLs to delicious"""

from include.useragent import UserAgent
from urllib2 import HTTPPasswordMgrWithDefaultRealm, HTTPBasicAuthHandler
from urlparse import urljoin
from include.utils import Module, Base
import sys
import re

class Delicious(Base):
    """Simple API frontend"""

    baseurl = 'https://api.del.icio.us/'
    posturl = urljoin(baseurl, '/v1/posts/add')
    opts = {
        'url': None,
        'description': 'posted from madcow',
        'tags': ['madcow'],
        'replace': 'no',
        'shared': 'yes',
    }.items()
    code = re.compile(r'code="(.*?)"')

    def __init__(self, username, password):
        password_mgr = HTTPPasswordMgrWithDefaultRealm()
        password_mgr.add_password(None, self.posturl, username, password)
        auth_handler = HTTPBasicAuthHandler(password_mgr)
        self.ua = UserAgent(handlers=[auth_handler])

    def post(self, url, tags):
        opts = dict(self.opts)
        opts['url'] = url
        opts['tags'] += tags
        opts['tags'] = ' '.join(opts['tags'])
        result = self.ua.openurl(self.posturl, opts=opts)
        code = self.code.search(result).group(1)
        print >> sys.stderr, '%s -> delicious: %s' % (url, code)


class Main(Module):
    pattern = re.compile(r'^(.+)$')
    require_addressing = False
    url = re.compile(r'https?://\S+', re.I)

    def __init__(self, madcow=None):
        try:
            username = madcow.config.delicious.username
            password = madcow.config.delicious.password
        except:
            username = ''
            password = ''
        if not username and not password:
            self.enabled = False
            return
        self.delicious = Delicious(username, password)

    def response(self, nick, args, **kwargs):
        try:
            for url in self.url.findall(args[0]):
                self.delicious.post(url, nick)
        except Exception, e:
            print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
            return '%s: problem with query: %s' % (nick, e)

