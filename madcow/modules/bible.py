#!/usr/bin/env python

"""LOLXIANS"""

from urlparse import urljoin
from random import choice
import re
from madcow.util.http import getsoup
from madcow.util import Module, strip_html, superscript

class Main(Module):

    pattern = re.compile(r'^\s*(?:(list bibles)|'             # list bibles
                          'bible\s+(.+?\s+\d+:\d+(?:-\d+)?)'  # get verse
                          '(?:\s+(\S+))?)\s*$', re.I)         # optional book
    help = 'bible <ch>:<verse>[-verse] [book] - see what god has to say'
    help += '\nlist bibles - get list of bibles available'

    bg_url = 'http://www.biblegateway.com/'
    bg_search = urljoin(bg_url, '/passage/')
    sup_re = re.compile(r'<sup[^>]*>(.*?)</sup>', re.I | re.DOTALL)

    DEFAULT_BIBLE = 'KJV'  # king james.. hella inaccurate but florid language

    # only a subset of available books work at all with BeautifulSoup..
    # I believe this to be a case of unicode being seriously fucked up
    # on the website.. the values below seem to bare that out, as they
    # are mostly nonsense mixture of some latin1 and some utf-8
    # i really don't care about this module enough at this point to make
    # this shit work better..  GOD IS DEAD

    bibles = {'AA': u'Jo\xe3o Ferreira de Almeida Atualizada',
              'ALAB': u'Arabic Life Application Bible',
              'ALB': u'Albanian Bible',
              'AMP': u'Amplified Bible',
              'AMU': u'Amuzgo de Guerrero',
              'ASV': u'American Standard Version',
              'BDS': u'La Bible du Semeur',
              'BG1940': u'1940 Bulgarian Bible',
              'BULG': u'Bulgarian Bible',
              'CCO': u'Chinanteco de Comaltepec',
              'CEV': u'Contemporary English Version',
              'CKW': u'Cakchiquel Occidental',
              'CRO': u'Croatian Bible',
              'CST': u'Castilian',
              'CUV': u'Chinese Union Version (Traditional)',
              'CUVS': u'Chinese Union Version (Simplified)',
              'DARBY': u'Darby Translation',
              'DN1933': u'Dette er Biblen p\xc3\xa5 dansk',
              'DNB1930': u'Det Norsk Bibelselskap 1930',
              'ESV': u'English Standard Version',
              'GW': u'GOD\u2019S WORD Translation',
              'HCSB': u'Holman Christian Standard Bible',
              'HCV': u'Haitian Creole Version',
              'HLGN': u'Hiligaynon Bible',
              'HOF': u'Hoffnung f\xfcr Alle',
              'HTB': u'Het Boek',
              'ICELAND': u'Icelandic Bible',
              'JAC': u'Jacalteco, Oriental',
              'KAR': u'Hungarian K\xc3\xa1roli',
              'KEK': u'Kekchi',
              'KJ21': u'21st Century King James Version',
              'KJV': u'King James Version',
              'LB': u'Levande Bibeln',
              'LBLA': u'La Biblia de las Am\xe9ricas',
              'LM': u'La Parola \xe8 Vita',
              'LND': u'La Nuova Diodati',
              'LSG': u'Louis Segond',
              'LUTH1545': u'Luther Bibel 1545',
              'MAORI': u'Maori Bible',
              'MNT': u'Macedonian New Testament',
              'MSG': u'The Message',
              'MVC': u'Mam, Central',
              'MVJ': u'Mam de Todos Santos Chuchumat\xe1n',
              'NASB': u'New American Standard Bible',
              'NCV': u'New Century Version',
              'NGU': u'N\xe1huatl de Guerrero',
              'NIRV': u"New International Reader's Version",
              'NIV': u'New International Version',
              'NIVUK': u'New International Version - UK',
              'NKJV': u'New King James Version',
              'NLT': u'New Living Translation',
              'NPK': u'N\xe1dej pre kazd\xe9ho',
              'NVI': u'Nueva Versi\xf3n Internacional',
              'OL': u'O Livro',
              'QUT': u'Quich\xe9, Centro Occidental',
              'REIMER': u'Reimer 2001',
              'RMNN': u'Romanian',
              'RUSV': u'Russian Synodal Version',
              'RVA': u'Reina-Valera Antigua',
              'RVR1960': u'Reina-Valera 1960',
              'RVR1995': u'Reina-Valera 1995',
              'SNC': u'Slovo na cestu',
              'SND': u'Ang Salita ng Diyos',
              'SNT': u'Swahili New Testament',
              'SV1917': u'Svenska 1917',
              'SVL': u'Levande Bibeln',
              'SZ': u'Slovo Zhizny',
              'TLA': u'Traducci\xf3n en lenguaje actual',
              'TLCR': u'Romanian',
              'TNIV': u"Today's New International Version",
              'TR1550': u'1550 Stephanus New Testament',
              'TR1894': u'1894 Scrivener New Testament',
              'UKR': u'Ukrainian Bible',
              'USP': u'Uspanteco',
              'VIET': u'1934 Vietnamese Bible',
              'WE': u'Worldwide English (New Testament)',
              'WHNU': u'1881 Westcott-Hort New Testament',
              'WLC': u'The Westminster Leningrad Codex',
              'WYC': u'Wycliffe New Testament',
              'YLT': u"Young's Literal Translation"}

    error = [u'God did not like that.',
             u"Watch it, you're just pissing God off now.",
             u'Consider yourself smited for that blasphemous query.',
             u'Go to hell.',
             ]

    def response(self, nick, args, kwargs):
        list_bibles, query, book = args
        if list_bibles:
            kwargs['req'].make_private()
            return self.list_bibles()
        else:
            return u'%s: %s' % (nick, self.lookup_verse(query, book))

    def list_bibles(self):
        """Get list of bibles available"""
        ksize = len(max(self.bibles, key=lambda key: len(key)))
        fmt = u'%%%ds - %%s' % ksize
        return u'\n'.join(fmt % item for item in self.bibles.iteritems())

    def lookup_verse(self, query, book=None):
        """Lookup specified verse"""
        if book is None:
            book = self.DEFAULT_BIBLE
        elif book not in self.bibles:
            return u'Unknown bible.. why do you hate god so much?'
        opts = {'search': query, 'version': book}
        soup = getsoup(self.bg_search, opts, referer=self.bg_search)
        res = soup.body.find('div', 'result-text-style-normal')
        res = res.renderContents().decode('utf-8', 'ignore')

        # convert superscript verse markers to unicode
        while True:
            match = self.sup_re.search(res)
            if not match:
                break
            res = res.replace(match.group(0),
                              superscript(match.group(1)))

        return strip_html(res).strip()
