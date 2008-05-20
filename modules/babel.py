#!/usr/bin/env python

"""Use AV's babel translator for language conversion"""

import re
from include.utils import Module
from include.useragent import posturl
from urlparse import urljoin
import sys

class Main(Module):
    pattern = re.compile('^\s*(list languages|translate)(?:\s+from\s+(\w+)\s+to\s+(\w+)\s*[-:]\s*(.+))?$', re.I)
    require_addressing = True
    help = 'list languages - list translate languages available\n'
    help += 'translate from <lang> to <lang>: text'
    re_translate = re.compile(r'<div id="result"><div.*?>(.*?)</div>')
    languages = {
        'chinese-simp': 'zh',
        'chinese-trad': 'zt',
        'chinese': 'zh',
        'dutch': 'nl',
        'english': 'en',
        'french': 'fr',
        'german': 'de',
        'greek': 'el',
        'italian': 'it',
        'japanese': 'ja',
        'korean': 'ko',
        'portuguese': 'pt',
        'russian': 'ru',
        'spanish': 'es',
    }
    baseurl = 'http://babelfish.yahoo.com/'
    translate = urljoin(baseurl, '/translate_txt')
    unknown =  "I don't know that language, try: list languages"

    def response(self, nick, args, **kwargs):
        try:
            if args[0] == 'list languages':
                return '%s: %s' % (nick, ', '.join(self.languages.keys()))

            try:
                from_lang = self.languages[args[1].lower()]
                to_lang = self.languages[args[2].lower()]
            except:
                return '%s: %s' % (nick, self.unknown)

            opts = {
                'ei': 'UTF-8',
                'doit': 'done',
                'fr': 'bf-home',
                'intl': '1',
                'tt': 'urltext',
                'trtext': args[3],
                'lp': '%s_%s' % (from_lang, to_lang),
                'btnTrTxt': 'Translate',
            }

            doc = posturl(self.translate, opts=opts)
            translated = self.re_translate.search(doc).group(1)
            return '%s: %s' % (nick, translated)
        except Exception, e:
            print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
            return "%s: Couldn't translate for some reason :/" % nick


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
