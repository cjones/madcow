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

"""Spellcheck using google"""

from include.utils import Module
import logging as log
import re
from include.google import Google

__version__ = '0.1'
__author__ = 'cj_ <cjones@gruntle.org>'
__all__ = []

class Main(Module):
    pattern = re.compile(r'^\s*spell(?:\s*check)?\s+(.+?)\s*$', re.I)
    help = 'spellcheck <word> - use google to spellcheck'

    def __init__(self, madcow=None):
        self.google = Google()

    def response(self, nick, args, kwargs):
        try:
            query = args[0]
            corrected = self.google.spellcheck(query)
            if query.lower() == corrected.lower():
                result = 'spelled correctly'
            else:
                result = corrected
            return '%s: %s' % (nick, result)
        except Exception, e:
            log.warn('error in %s: %s' % (self.__module__, e))
            log.exception(e)
            return '%s: %s' % (nick, self.error)


if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)
