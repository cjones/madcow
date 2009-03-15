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

"""Get a random confession from fmylife.com"""

from include.utils import Module, stripHTML
from include.useragent import geturl
import logging as log
import re

class Main(Module):

    pattern = re.compile(u'^\s*fml\s*(\d+)?\s*$', re.I)
    require_addressing = True
    help = u'fml - misery from fmylife.com'
    rand_url = 'http://api.betacie.com/view/random?key=readonly&language=en'
    spec_url = 'http://api.betacie.com/view/%d/nocomment?key=readonly&language=en'
    regex = re.compile(r'<text>(.*)</text>')
    
    def response(self, nick, args, kwargs):
        try:
            if args[0]:
                url = self.spec_url % int(args[0])
            else:
                url = self.rand_url
            doc = geturl(url)
            text = self.regex.search(doc).group(1)
            return stripHTML(text)
        except Exception, error:
            log.warn(u'error in module %s' % self.__module__)
            log.exception(error)
            return u'%s: Today I couldn\'t seem to access fmylife.com.. FML' % nick


if __name__ == u'__main__':
    from include.utils import test_module
    test_module(Main)
