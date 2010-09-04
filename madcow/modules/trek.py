#!/usr/bin/env python
#
# Copyright (C) 2007-2008 Christopher Jones
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

"""Star Trek failure generator"""

from include.BeautifulSoup import BeautifulSoup
from include.useragent import geturl
from include.utils import stripHTML
from include.utils import Module
import logging as log
import re

__version__ = '0.1'
__author__ = 'Chris Jones <cjones@gruntle.org>'
__all__ = ['TrekFailure']

class TrekFailure(Module):

    pattern = re.compile(r'^\s*(?:star\s*)?trek\s*$', re.I)
    help = u'trek - generate technobabble'
    url = 'http://hyotynen.kapsi.fi/trekfailure/'
    fail_re = re.compile(r'^[ \n]*- (.*?) -[ \n]*$')
    spaces_re = re.compile(r'\s{2,}')

    def __init__(self, madcow):
        self.col = madcow.colorlib.get_color

    def response(self, nick, args, kwargs):
        try:
            fail = BeautifulSoup(geturl(self.url)).h1
            return self.spaces_re.sub(' ', stripHTML(
                u'%s: %s: %s %s: %s' % (
                    nick, self.col('red', text='FAIL'),
                    self.fail_re.search(fail.renderContents()).group(1),
                    self.col('green', text='FIX'),
                    self.fail_re.search(
                        fail.findNext('h1').renderContents()).group(1))))
        except Exception, error:
            log.warn('error in module %s' % self.__module__)
            log.exception(error)
            return u'%s: Too much fail for technobabble' % (nick, error)

Main = TrekFailure

if __name__ == u'__main__':
    from include.utils import test_module
    test_module(Main)
