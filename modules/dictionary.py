#!/usr/bin/env python

# Lookup a definition in the dictionary... btw, hardest module to write ever.. HTML scraping sucks :(

import sys
import re
import urllib
from include import utils

# class for this module
class MatchObject(object):
    def __init__(self, config=None, ns='default', dir=None):
        self.enabled = True                # True/False - enabled?
        self.pattern = re.compile('^\s*define\s+(\w+)(?:\s+(\d+))?$')
        self.requireAddressing = True            # True/False - require addressing?
        self.thread = True                # True/False - should bot spawn thread?
        self.wrap = True                # True/False - wrap output?
        self.help = 'define <word/phrase> [#] - get a definition from merriam-webster'

        self.defLineA = re.compile('<div class="word_definition">(.*?)</div>', re.DOTALL)
        self.defLineB = re.compile('^(<b>.+)$', re.MULTILINE)
        self.newline = re.compile('<br>')
        self.hasJS = re.compile('javascript')
        self.header = re.compile('^.*?:\s+')

    # function to generate a response
    def response(self, *args, **kwargs):
        nick = kwargs['nick']
        args = kwargs['args']
        try:
            word = args[0].lower()
            try:
                if len(args) > 1: num = int(args[1])
                else: num = 1
            except:
                num = 1

            url = 'http://www.m-w.com/dictionary/' + word
            doc = urllib.urlopen(url).read()
            doc = self.defLineA.search(doc).group(1)
            doc = self.defLineB.search(doc).group(1)
            defs = [utils.stripHTML(d) for d in self.newline.split(doc)]
            defs = [self.header.sub('', definition) for definition in defs]

            if num > len(defs): num = 1
            return '%s: [%s/%s] %s' % (nick, num, len(defs), defs[num - 1])
        except Exception, e:
            print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
            return "%s: I couldn't look that up for some reason.  D:" % nick
        


# this is just here so we can test the module from the commandline
def main(argv = None):
    if argv is None: argv = sys.argv[1:]
    obj = MatchObject()
    print obj.response(nick='testUser', args=argv)

    return 0

if __name__ == '__main__': sys.exit(main())
