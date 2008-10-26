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

"""I'm feeling lucky"""

from include.google import Google
from include.utils import Module
import re
import logging as log

__version__ = '0.3'
__author__ = 'cj_ <cjones@gruntle.org>'

class Main(Module):

    pattern = re.compile('^\s*google\s+(.*?)\s*$')
    require_addressing = True
    help = "google <query> - i'm feeling lucky"

    def __init__(self, *args, **kwargs):
        self.google = Google()

    def response(self, nick, args, kwargs):
        try:
            query = args[0]
            return '%s: %s = %s' % (nick, query, self.google.lucky(query))
        except Exception, error:
            log.warn('error in module %s' % self.__module__)
            log.exception(error)
            return '%s: Not so lucky today..' % nick


if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)
