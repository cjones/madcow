#!/usr/bin/env python

"""Lookup a definition in the dictionary..."""

import sys
import re
from include.utils import stripHTML, Module
from include.useragent import geturl
from urlparse import urljoin

class Main(Module):
    pattern = re.compile('^\s*define\s+(\w+)(?:\s+(\d+))?$')
    require_addressing = True
    help = 'define <word/phrase> [#] - get a definition from merriam-webster'

    re_defs = re.compile(r'<div class="defs">(.*?)</div>', re.DOTALL)
    re_newline = re.compile(r'[\r\n]+')
    re_def_break = re.compile(r'<span class="sense_break"/>')
    header = re.compile('^.*?:\xa0')
    base_url = 'http://www.m-w.com/dictionary/'

    def response(self, nick, args, **kwargs):
        word = args[0].lower()
        try:
            try:
                num = int(args[1])
            except:
                num = 1

            url = urljoin(self.base_url, word)
            doc = geturl(url)
            defs = self.re_defs.search(doc).group(1)
            defs = self.re_newline.sub('', defs)
            defs = self.re_def_break.split(defs)
            if len(defs) > 1:
                defs.pop(0)
            if num > len(defs):
                num = 1
            definition = defs[num - 1]
            definition = stripHTML(definition)
            definition = self.header.sub('', definition)

            return '%s: [%s/%s] %s' % (nick, num, len(defs), definition)

        except Exception, e:
            print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
            return "%s: I couldn't look that up for some reason.  D:" % nick


def main():
    try:
        main = Main()
        args = main.pattern.search(' '.join(sys.argv[1:])).groups()
        print main.response(nick=os.environ['USER'], args=args)
    except Exception, e:
        print 'no match: %s' % e

if __name__ == '__main__':
    import os
    sys.exit(main())
