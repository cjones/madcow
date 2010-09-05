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

"""Look up drink mixing ingredients"""

import re
from madcow.util import Module, strip_html
from madcow.util.http import geturl
from urlparse import urljoin


class Main(Module):

    pattern = re.compile(u'^\s*drinks?\s+(.+)', re.I)
    require_addressing = True
    help = u'drinks <drink name> - look up mixing instructions'
    baseurl = u'http://www.webtender.com/'
    search = urljoin(baseurl, u'/cgi-bin/search')
    drink = re.compile(u'<A HREF="(/db/drink/\d+)">')
    title = re.compile(u'<H1>(.*?)<HR></H1>')
    ingredients = re.compile(u'<LI>(.*?CLASS=ingr.+)')
    instructions = re.compile(u'<H3>Mixing instructions:</H3>.*?<P>(.*?)</P>',
                              re.DOTALL)

    def response(self, nick, args, kwargs):
        query = args[0]
        try:
            doc = geturl(self.search, opts={u'verbose': u'on', u'name': query})
            drink = self.drink.search(doc).group(1)
            url = urljoin(self.baseurl, drink)
            doc = geturl(url)
            title = self.title.search(doc).group(1)
            ingredients = self.ingredients.findall(doc)
            instructions = self.instructions.search(doc).group(1)
            response = u'%s: %s - %s - %s' % (
                    nick, title, u', '.join(ingredients), instructions)
            response = strip_html(response)
            return response
        except Exception, error:
            self.log.warn(u'error in module %s' % self.__module__)
            self.log.exception(error)
            return u"%s: Something ungood happened looking that up, sry" % nick


if __name__ == u'__main__':
    from madcow.util import test_module
    test_module(Main)
