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

"""Get a random confession from grouphug.us"""

import re
from include.utils import Module, stripHTML
from include.useragent import geturl
from include.BeautifulSoup import BeautifulSoup
from urlparse import urljoin
import random
import logging as log

class Main(Module):

    pattern = re.compile(u'^\s*hugs\s*$', re.I)
    require_addressing = True
    help = u'hugs - random confession'
    baseurl = u'http://beta.grouphug.us/'
    random = urljoin(baseurl, u'/random')
    last = re.compile(r'<a href="/frontpage\?page=(\d+)" class="pager-last ac'
                      r'tive"')

    def response(self, nick, args, kwargs):
        try:
            # XXX site is all broken at the moment, so do this instead..
            doc = geturl(self.baseurl)
            last = int(self.last.search(doc).group(1))
            page = random.randint(1, last)
            url = urljoin(self.baseurl, '/frontpage?page=%d' % page)
            doc = geturl(url)
            #doc = geturl(self.random)

            soup = BeautifulSoup(doc)
            main = soup.find(u'div', attrs={u'id': u'main'})
            confs = main.findAll(u'div', attrs={u'class': u'content'})
            conf = random.choice(confs)
            conf = [unicode(p) for p in conf.findAll(u'p')]
            conf = u' '.join(conf)
            conf = stripHTML(conf)
            conf = conf.strip()
            return conf
        except Exception, error:
            log.warn(u'error in module %s' % self.__module__)
            log.exception(error)
            return u'%s: I had some issues with that..' % nick


if __name__ == u'__main__':
    from include.utils import test_module
    test_module(Main)
