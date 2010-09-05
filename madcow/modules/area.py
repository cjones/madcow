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

"""This module looks up area codes and returns the most likely city"""

import re
from madcow.util import Module
from madcow.util.http import getsoup
import logging as log

def render(node):
    return node.renderContents().decode('utf-8', 'ignore').strip()


def proper(name):
    return ' '.join(word.capitalize() for word in name.split())


class Main(Module):

    pattern = re.compile(u'^\s*area(?:\s+code)?\s+(\d+)\s*', re.I)
    require_addressing = True
    help = u'area <areacode> - what city does it belong to'
    url = 'http://www.melissadata.com/lookups/ZipCityPhone.asp'

    def response(self, nick, args, kwargs):
        try:
            soup = getsoup(self.url, {'InData': args[0]})
            city = soup.body.find('table', bgcolor='#ffffcc').a
            return u'%s: %s: %s, %s' % (
                    nick, args[0], proper(render(city).capitalize()),
                    proper(render(city.parent.findNext('td'))))
            return u''
        except Exception, error:
            log.warn(u'error in module %s' % self.__module__)
            log.exception(error)
            return u"%s: I couldn't look that up for some reason.  D:" % nick


if __name__ == u'__main__':
    import sys
    sys.argv.append('area 707')
    from madcow.util import test_module
    test_module(Main)
