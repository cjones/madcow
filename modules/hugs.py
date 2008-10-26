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

    pattern = re.compile('^\s*hugs\s*$', re.I)
    require_addressing = True
    help = 'hugs - random confession'
    baseurl = 'http://beta.grouphug.us/'
    random = urljoin(baseurl, '/random')

    def response(self, nick, args, kwargs):
        try:
            doc = geturl(self.random)
            soup = BeautifulSoup(doc)
            main = soup.find('div', attrs={'id': 'main'})
            confs = main.findAll('div', attrs={'class': 'content'})
            conf = random.choice(confs)
            conf = [str(p) for p in conf.findAll('p')]
            conf = ' '.join(conf)
            conf = stripHTML(conf)
            conf = conf.strip()
            return conf
        except Exception, error:
            log.warn('error in %s: %s' % (self.__module__, error))
            log.exception(error)
            return '%s: I had some issues with that..' % nick


if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)
