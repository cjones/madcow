#!/usr/bin/env python
#
# Copyright (C) 2007, 2008 Christopher Jones
#
# This file is part of Madcow.
#
# Madcow is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Madcow is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Madcow.  If not, see <http://www.gnu.org/licenses/>.

"""Post URLs to delicious"""

from useragent import UserAgent
from urllib2 import HTTPPasswordMgrWithDefaultRealm, HTTPBasicAuthHandler
from urlparse import urljoin
from utils import Module, stripHTML
import re
import logging as log

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
            username = madcow.config.delicious.username
            password = madcow.config.delicious.password
        except:
            username = u''
            password = u''
        if not username or not password:
            self.enabled = False
            return
        self.delicious = Delicious(username, password)

    def response(self, nick, args, kwargs):
        try:
            for url in self.url.findall(args[0]):
                self.delicious.post(url, tags=[nick])
        except Exception, error:
            # XXX meh.. people post jokey urls a lot, no point spamming logs
            #log.warn(u'error in module %s' % self.__module__)
            #log.exception(error)
            pass

