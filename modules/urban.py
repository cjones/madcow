#!/usr/bin/env python

"""
Look up a definition in the Urban Dictionary
"""

import sys
import re
import SOAPpy
import os


class MatchObject(object):

    def __init__(self, config=None, ns='madcow', dir=None):
        self.enabled = True
        self.pattern = re.compile('^\s*urban\s+(.+)')
        self.requireAddressing = True
        self.thread = True
        self.wrap = True
        self.help = 'urban <phrase> - look up a word/phrase on urban dictionary'

        self.key = 'a979884b386f8b7ea781754892f08d12'
        self.server = SOAPpy.SOAPProxy("http://api.urbandictionary.com/soap")

    def response(self, **kwargs):
        nick = kwargs['nick']
        args = kwargs['args']

        try:
            words = args[0].split()
            if words[-1].isdigit():
                i = int(words[-1])
                term = ' '.join(words[:-1])
            else:
                i = 1
                term = ' '.join(words)


            items = self.server.lookup(self.key, term)

            max = len(items)
            if max == 0:
                return "%s: So obscure even urban dictionary doesn't know what it means" % nick

            if i > max:
                return '%s: CRITICAL BUFFER OVERFLOW ERROR' % nick

            item = items[i - 1]
            response = '%s: [%s/%s] %s - Example: %s' % (nick, i, max, item.definition, item.example)
            return response.encode("utf-8")

        except Exception, e:
            print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
            return "%s: Serious problems: %s" % (nick, e)


if __name__ == '__main__':
    print MatchObject().response(nick=os.environ['USER'], args=[' '.join(sys.argv[1:])])
    sys.exit(0)
