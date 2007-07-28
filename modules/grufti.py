#!/usr/bin/env python

"""
Implement Grufti trigger/response spam
"""

import sys
import re
import os
import random


class MatchObject(object):
    reMatchBlocks = re.compile('%match\s+(.*?)%end', re.DOTALL)
    reCommaDelim = re.compile('\s*,\s*')
    rePipeDelim = re.compile('\s*\|\s*')
    reToken = re.compile('({{\s*(.*?)\s*}})')
    reIsRegex = re.compile('^/(.+)/$')

    def __init__(self, config=None, ns='madcow', dir=None):
        self.enabled = True
        self.pattern = re.compile('^(.+)$')
        self.requireAddressing = False
        self.thread = False
        self.wrap = False

        self.data = []

        if dir is None:
            dir = os.path.abspath(os.path.dirname(sys.argv[0]))
        file = dir + '/grufti-responses.txt'

        try:
            fi = open(file)
            doc = fi.read()
            fi.close()

            for block in self.reMatchBlocks.findall(doc):
                responses = block.splitlines()
                matchString = responses.pop(0)
                if len(responses) == 0: continue
                matches = []
                for match in self.reCommaDelim.split(matchString):
                    isRegex = self.reIsRegex.search(match)
                    if isRegex is not None:
                        regex = re.compile(isRegex.group(1), re.I)
                    else:
                        regex = re.compile(r'\b' + re.escape(match) + r'\b', re.I)

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

    def response(self, **kwargs):
        try:
            nick = kwargs['nick']
            args = kwargs['args']

            for matches, responses in self.data:
                for match in matches:
                    if match.search(args[0]) is not None:
                        return self.parseTokens(random.choice(responses))

        except Exception, e:
            print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)


if __name__ == '__main__':
    print MatchObject(dir='..').response(nick=os.environ['USER'], args=[' '.join(sys.argv[1:])])
    sys.exit(0)
