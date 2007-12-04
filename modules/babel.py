#!/usr/bin/env python

"""
Use AV's babel translator for language conversion
"""

import sys
import re
import urllib
import os


class MatchObject(object):

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

    def __init__(self, config=None, ns='madcow', dir='..'):
        self.enabled = True
        self.pattern = re.compile('^\s*(list languages|translate)(?:\s+from\s+(\w+)\s+to\s+(\w+)\s*[-:]\s*(.+))?$', re.I)
        self.requireAddressing = True
        self.thread = True
        self.wrap = True
        self.help = 'list languages - list translate languages available\n'
        self.help += 'translate from <lang> to <lang>: text'

    def response(self, **kwargs):
        nick = kwargs['nick']
        args = kwargs['args']

        try:
            if args[0] == 'list languages':
                return '%s: %s' % (nick, ', '.join(MatchObject.languages.keys()))

            try:
                fromLang = MatchObject.languages[args[1].lower()]
                toLang = MatchObject.languages[args[2].lower()]
            except:
                return "%s: I don't know that language, try: list languages" % nick

            url = 'http://babelfish.altavista.com/tr?' + urllib.urlencode({
                'doit': 'done',
                'intl': 1,
                'tt': 'urltext',
                'trtext': args[3],
                'lp': '%s_%s' % (fromLang, toLang),
                'btnTrTxt': 'Translate',
            })

            doc = urllib.urlopen(url).read()
            translated = MatchObject.reTranslated.search(doc).group(1)
            return '%s: %s' % (nick, translated)

        except Exception, e:
            print >> sys.stderr, 'error in %s: %s' % (self.__module__, e)
            return "%s: I couldn't make that translation for some reason :/" % nick


if __name__ == '__main__':
    print MatchObject().response(nick=os.environ['USER'], args=sys.argv[1:])
    sys.exit(0)
