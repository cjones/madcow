#!/usr/bin/env python

"""
Lookup a definition in the dictionary...
"""

import sys
import re
import urllib
from include import utils
import os


class MatchObject(object):

    def __init__(self, config=None, ns='madcow', dir=None):
        self.enabled = True
        self.pattern = re.compile('^\s*define\s+(\w+)(?:\s+(\d+))?$')
        self.requireAddressing = True
        self.thread = True
        self.wrap = True
        self.help = 'define <word/phrase> [#] - get a definition from merriam-webster'

        self.re_defs = re.compile(r'<div class="defs">(.*?)</div>', re.DOTALL)
        self.re_newline = re.compile(r'[\r\n]+')
        self.re_def_break = re.compile(r'<span class="sense_break"/>')
        self.header = re.compile('^.*?:\xa0')

    def response(self, **kwargs):
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
            defs = self.re_defs.search(doc).group(1)
            defs = self.re_newline.sub('', defs)
            defs = self.re_def_break.split(defs)
            if len(defs) > 1:
                defs.pop(0)
            defs = [utils.stripHTML(d) for d in defs]
            defs = [self.header.sub('', definition) for definition in defs]

            if num > len(defs):
                num = 1

            return '%s: [%s/%s] %s' % (nick, num, len(defs), defs[num - 1])

        except Exception, e:
            print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
            return "%s: I couldn't look that up for some reason.  D:" % nick


if __name__ == '__main__':
    print MatchObject().response(nick=os.environ['USER'], args=sys.argv[1:])
    sys.exit(0)
