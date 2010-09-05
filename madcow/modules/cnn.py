#!/usr/bin/env python
#
# Copyright (C) 2009 Christopher Jones
#
# This file is part of Madcow.
#
# Madcow is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# Madcow is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License
# along with Madcow.  If not, see <http://www.gnu.org/licenses/>.

"""CNN Headline"""

from utils import Module
import logging as log
import re
from import feedparser
#from useragent import geturl   # mimic browser
from utils import stripHTML    # strip HTML/unescape entities

__version__ = u'0.1'
__author__ = u'Chris Jones <cjones@gruntle.org>'
__all__ = []

class Main(Module):

    pattern = re.compile(r'^\s*cnn\s*$', re.I)
    help = 'cnn - cnn headline'
    url = 'http://rss.cnn.com/rss/cnn_topstories.rss'

    def response(self, nick, args, kwargs):
        try:
            item = feedparser.parse(self.url).entries[0]
            body = stripHTML(item.description).strip()
            return u' | '.join([item.link, body, item.updated])
        except Exception, error:
            log.warn(u'error in module %s' % self.__module__)
            log.exception(error)
            return u'%s: %s' % (nick, error)


if __name__ == u'__main__':
    from utils import test_module
    test_module(Main)
