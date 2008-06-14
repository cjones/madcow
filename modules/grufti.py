#!/usr/bin/env python

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
            filename = os.path.join(madcow.dir, 'grufti-responses.txt')
            if not os.path.exists(filename):
                sample = os.path.join(madcow.dir, self._sample)
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
        except Exception, e:
            log.warn('error in %s: %s' % (self.__module__, e))
            log.exception(e)
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

        except Exception, e:
            log.warn('error in %s: %s' % (self.__module__, e))
            log.exception(e)

