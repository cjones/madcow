#!/usr/bin/env python

"""Use AV's babel translator for language conversion"""

import sys
import re
import os
from include.utils import Base, UserAgent
from urlparse import urljoin

class Main(Base):
    enabled = True
    pattern = re.compile('^\s*(list languages|translate)(?:\s+from\s+(\w+)\s+to\s+(\w+)\s*[-:]\s*(.+))?$', re.I)
    require_addressing = True


    help = 'list languages - list translate languages available\n'
    help += 'translate from <lang> to <lang>: text'

    reTranslated = re.compile('<td bgcolor=white class=s><div style=padding:10px;>(.*?)</div></t', re.DOTALL)
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
    _base_url = 'http://babelfish.altavista.com/'
    _trans_url = urljoin(_base_url, '/tr')
    _unknown =  "I don't know that language, try: list languages"

    def __init__(self, madcow=None):
        self.madcow = madcow
        self.ua = UserAgent()

    def response(self, **kwargs):
        nick = kwargs['nick']
        args = kwargs['args']

        try:
            if args[0] == 'list languages':
                return '%s: %s' % (nick, ', '.join(self.languages.keys()))

            try:
                fromLang = self.languages[args[1].lower()]
                toLang = self.languages[args[2].lower()]
            except:
                return '%s: %s' % (nick, self._unknown)

            opts = {
                'doit': 'done',
                'intl': 1,
                'tt': 'urltext',
                'trtext': args[3],
                'lp': '%s_%s' % (fromLang, toLang),
                'btnTrTxt': 'Translate',
            }

            doc = self.ua.fetch(self._trans_url, opts=opts)
            translated = self.reTranslated.search(doc).group(1)
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
    sys.exit(main())
