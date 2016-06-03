#!/usr/bin/env python

"""Translation service using Google Translate"""

import re
import simplejson
from madcow.util import strip_html
from madcow.util.http import geturl
from madcow.util import Module

class BabelError(Exception):

    """Raised to stop translation due to internal error"""


class Main(Module):

    """Translation service using Google Translate"""

    pattern = re.compile(r'^\s*(translate\s+(.+?)|list\s+lang(s|uages)?)\s*$', re.I)
    help = '\n'.join([
        'translate: <text> - auto-detect language and convert to english',
        'translate: from <lang> to <lang> [to <lang> ...]: text - specify translation',
        'list languages - list all available languages',
        ])
    default_lang = 'english'
    #url = 'http://ajax.googleapis.com/ajax/services/language/translate'

    langs = {'auto': '',
             'afrikaans': 'af',
             'albanian': 'sq',
             'amharic': 'am',
             'arabic': 'ar',
             'armenian': 'hy',
             'azerbaijani': 'az',
             'basque': 'eu',
             'belarusian': 'be',
             'bengali': 'bn',
             'bihari': 'bh',
             'bulgarian': 'bg',
             'burmese': 'my',
             'catalan': 'ca',
             'cherokee': 'chr',
             'chinese': 'zh',
             'chinese_simplified': 'zh-CN',
             'chinese_traditional': 'zh-TW',
             'croatian': 'hr',
             'czech': 'cs',
             'danish': 'da',
             'dhivehi': 'dv',
             'dutch': 'nl',
             'english': 'en',
             'esperanto': 'eo',
             'estonian': 'et',
             'filipino': 'tl',
             'finnish': 'fi',
             'french': 'fr',
             'galician': 'gl',
             'georgian': 'ka',
             'german': 'de',
             'greek': 'el',
             'guarani': 'gn',
             'gujarati': 'gu',
             'hebrew': 'iw',
             'hindi': 'hi',
             'hungarian': 'hu',
             'icelandic': 'is',
             'indonesian': 'id',
             'inuktitut': 'iu',
             'irish': 'ga',
             'italian': 'it',
             'japanese': 'ja',
             'kannada': 'kn',
             'kazakh': 'kk',
             'khmer': 'km',
             'korean': 'ko',
             'kurdish': 'ku',
             'kyrgyz': 'ky',
             'laothian': 'lo',
             'latvian': 'lv',
             'lithuanian': 'lt',
             'macedonian': 'mk',
             'malay': 'ms',
             'malayalam': 'ml',
             'maltese': 'mt',
             'marathi': 'mr',
             'mongolian': 'mn',
             'nepali': 'ne',
             'norwegian': 'no',
             'oriya': 'or',
             'pashto': 'ps',
             'persian': 'fa',
             'polish': 'pl',
             'portuguese': 'pt-PT',
             'punjabi': 'pa',
             'romanian': 'ro',
             'russian': 'ru',
             'sanskrit': 'sa',
             'serbian': 'sr',
             'sindhi': 'sd',
             'sinhalese': 'si',
             'slovak': 'sk',
             'slovenian': 'sl',
             'spanish': 'es',
             'swahili': 'sw',
             'swedish': 'sv',
             'tagalog': 'tl',
             'tajik': 'tg',
             'tamil': 'ta',
             'telugu': 'te',
             'thai': 'th',
             'tibetan': 'bo',
             'turkish': 'tr',
             'uighur': 'ug',
             'ukrainian': 'uk',
             'urdu': 'ur',
             'uzbek': 'uz',
             'vietnamese': 'vi',
             'welsh': 'cy',
             'yiddish': 'yi'}

    lookup = dict((val, key) for key, val in langs.iteritems())

    def response(self, nick, args, kwargs):
        """Return a response to the bot to display"""
        if args[0].startswith('tr'):
            try:
                message = self.parse(args[1])
            except BabelError, error:
                self.log.error(error)
                message = error
            except Exception, error:
                self.log.warn('error in %s' % self.__module__)
                self.log.exception(error)
                message = error
        else:
            message = ', '.join(self.langs)
        return u'%s: %s' % (nick, message)

    def parse(self, cmd):
        """Parse command structure and transform text"""
        if ':' not in cmd:
            raise BabelError('missing text to translate')
        cmd, text = [arg.strip() for arg in cmd.split(':', 1)]
        cmd = cmd.lower().split()

        translations = []
        current_lang = None
        while cmd:
            arg = cmd.pop(0)
            if arg == 'from':
                continue
            elif arg in self.langs:
                if current_lang:
                    if arg == 'auto':
                        raise BabelError('can only auto-detect source')
                    if current_lang != arg:
                        translations.append((current_lang, arg))
                current_lang = arg
            elif arg == 'to':
                if not current_lang:
                    current_lang = 'auto'
            else:
                raise BabelError('unknown language: ' + arg)

        if not translations:
            translations = [('auto', self.default_lang)]
        for from_lang, to_lang in translations:
            text = self.translate(text, from_lang, to_lang)
        return text

    def translate(self, text, src, dst):
        """Perform the translation"""
        opts = {'q': text,
                'client': 't',
                'sl': 'en',
                'tl': 'es',
                'hl': 'en',
                'dt': 'at',
                'dt': 'bd',
                'dt': 'ex',
                'dt': 'ld',
                'dt': 'md',
                'dt': 'qca',
                'dt': 'rw',
                'dt': 'rm',
                'dt': 'ss',
                'dt': 't',
                'ie': 'UTF-8',
                'oe': 'UTF-8',
                'ssel': '3',
                'tsel': '3',
                'kc': '0',
                'tk': '286462.160648'}

        url = 'http://translate.google.com/translate_a/single'
        res = geturl(url, opts, referer='https://translate.google.com/')
        while u',,' in res:
            res = res.replace(u',,', u',"",')
        res = simplejson.loads(res)
        try:
            det = self.lookup[res[2]].capitalize()
        except StandardError:
            det = None
        while isinstance(res, list) and res:
            res = res[0]
        if src == 'auto' and det:
            res = u'[detected %s] %s' % (det, res)
        if res:
            return res
