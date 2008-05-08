#!/usr/bin/env python

"""Implement Grufti trigger/response spam"""

import sys
import re
import os
import random
from include.utils import Base, slurp

class Main(Base):
    enabled = True
    pattern = re.compile('^(.+)$')
    require_addressing = False



    reMatchBlocks = re.compile('%match\s+(.*?)%end', re.DOTALL)
    reCommaDelim = re.compile('\s*,\s*')
    rePipeDelim = re.compile('\s*\|\s*')
    reToken = re.compile('({{\s*(.*?)\s*}})')
    reIsRegex = re.compile('^/(.+)/$')

    def __init__(self, madcow=None):
        self.data = []
        filename = os.path.join(madcow.dir, 'grufti-responses.txt')

        try:
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
                        regex = re.compile(r'\b' + re.escape(match) + r'\b',
                                re.I)

                    matches.append(regex)

                self.data.append((matches, responses))

        except Exception, e:
            print >> sys.stderr, 'aborting load of grufti: %s' % e
            self.enabled = False

    def parseTokens(self, response):
        output = response
        for token, wordString in self.reToken.findall(response):
            word = random.choice(self.rePipeDelim.split(wordString))
            output = re.sub(re.escape(token), word, output, 1)

        return output

    def response(self, nick, args, **kwargs):
        try:
            for matches, responses in self.data:
                for match in matches:
                    if match.search(args[0]) is not None:
                        return self.parseTokens(random.choice(responses))

        except Exception, e:
            print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)


