"""Implement Grufti trigger/response spam"""

import re
import os
import random
from madcow.util import Module
import shutil
import encoding

class Main(Module):

    pattern = Module._any
    allow_threading = False
    priority = 100
    terminate = False
    require_addressing = False

    reMatchBlocks = re.compile(u'%match\s+(.*?)%end', re.DOTALL)
    reCommaDelim = re.compile(u'\s*,\s*')
    rePipeDelim = re.compile(u'\s*\|\s*')
    reToken = re.compile(u'({{\s*(.*?)\s*}})')
    reIsRegex = re.compile(u'^/(.+)/$')

    def init(self):
        self.data = []
        filename = os.path.join(self.madcow.base, 'response.grufti')
        if not os.path.exists(filename):
            raise ValueError
            shutil.copyfile(sample, filename)
            self.log.warn(u'created %s' % self._filename)
        with open(filename, 'rb') as fp:
            doc = fp.read()
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
                    regex = u''
                    if match[0].isalnum():
                        regex += r'\b'
                    regex += re.escape(match)
                    if match[-1].isalnum():
                        regex += r'\b'
                    regex = re.compile(regex, re.I)
                matches.append(regex)
            self.data.append((matches, responses))

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
                    if match.search(args[0]):
                        result = self.parseTokens(random.choice(responses))
                        return encoding.convert(result)

        except Exception, error:
            self.log.warn(u'error in %s: %s' % (self.__module__, error))
            self.log.exception(error)
