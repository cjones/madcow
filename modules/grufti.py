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

"""Implement Grufti trigger/response spam"""

import re
import os
import random
from include.utils import Module, slurp
import logging as log
import shutil

class Main(Module):

    pattern = Module._any
    allow_threading = False
    priority = 100
    terminate = False
    require_addressing = False
    reMatchBlocks = re.compile('%match\s+(.*?)%end', re.DOTALL)
    reCommaDelim = re.compile('\s*,\s*')
    rePipeDelim = re.compile('\s*\|\s*')
    reToken = re.compile('({{\s*(.*?)\s*}})')
    reIsRegex = re.compile('^/(.+)/$')
    _filename = 'grufti-responses.txt'
    _sample = _filename + '-sample'

    def __init__(self, madcow=None):
        try:
            self.data = []
            filename = os.path.join(madcow.prefix, 'grufti-responses.txt')
            if not os.path.exists(filename):
                sample = os.path.join(madcow.prefix, self._sample)
                shutil.copyfile(sample, filename)
                log.warn('created %s' % self._filename)
            doc = slurp(filename)
            for block in self.reMatchBlocks.findall(doc):
                responses = block.splitlines()
                matchString = responses.pop(0)
                if len(responses) == 0:
                    continue
                matches = []
                for match in self.reCommaDelim.split(matchString):
                    isRegex = self.reIsRegex.search(match)
                    if isRegex is not None:
                        regex = re.compile(isRegex.group(1), re.I)
                    else:
                        regex = ''
                        if match[0].isalnum():
                            regex += r'\b'
                        regex += re.escape(match)
                        if match[-1].isalnum():
                            regex += r'\b'
                        regex = re.compile(regex, re.I)
                    matches.append(regex)
                self.data.append((matches, responses))
        except Exception, error:
            log.warn('error in %s: %s' % (self.__module__, error))
            log.exception(error)
            self.enabled = False

    def parseTokens(self, response):
        output = response
        for token, wordString in self.reToken.findall(response):
            word = random.choice(self.rePipeDelim.split(wordString))
            output = re.sub(re.escape(token), word, output, 1)
        return output

    def response(self, nick, args, kwargs):
        try:
            for matches, responses in self.data:
                for match in matches:
                    if match.search(args[0]) is not None:
                        return self.parseTokens(random.choice(responses))

        except Exception, error:
            log.warn('error in %s: %s' % (self.__module__, error))
            log.exception(error)
