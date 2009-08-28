#!/usr/bin/env python
#
# Copyright (C) 2007-2008 Christopher Jones
#
# This file is part of Madcow.
#
# Madcow is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# Madcow is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
# for more details.
#
# You should have received a copy of the GNU General Public License
# along with Madcow.  If not, see <http://www.gnu.org/licenses/>.

"""LOLXIANS"""

from urlparse import urljoin
from random import choice
import logging as log
import re

from include.useragent import getsoup
from include.utils import Module, stripHTML, superscript

__version__ = '2.0'
__author__ = 'Chris Jones <cjones@gruntle.org>'
__all__ = []

class Main(Module):

    pattern = re.compile(r'^\s*(?:(list bibles)|'             # list bibles
                          'bible\s+(.+?\s+\d+:\d+(?:-\d+)?)'  # get verse
                          '(?:\s+(\S+))?)\s*$', re.I)         # optional book
    help = 'bible <book> <ch>:<verse>[-verse] [book] - see what god has to say'
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

    bibles = {'KOREAN': u'Korean Bible',
              'ICELAND': u'Icelandic Bible',
              'LSG': u'Louis Segond',
              'BDS': u'La Bible du Semeur',
              'CCO': u'Chinanteco de Comaltepec',
              'UKR': u'Ukrainian Bible',
              'SND': u'Ang Salita ng Diyos',
              'RUSV': u'Russian Synodal Version',
              'AMU': u'Amuzgo de Guerrero',
              'CRO': u'Croatian Bible',
              'TLCR': u'Romanian',
              'RMNN': u'Romanian',
              'SNT': u'Swahili New Testament',
              'WHNU': u'1881 Westcott-Hort New Testament',
              'JAC': u'Jacalteco, Oriental',
              'MVC': u'Mam, Central',
              'LND': u'La Nuova Diodati',
              'LM': u'La Parola \xe8 Vita',
              'AA': u'Jo\xe3o Ferreira de Almeida Atualizada',
              'OL': u'O Livro',
              'KAR': u'Hungarian K\xe1roli',
              'HCV': u'Haitian Creole Version',
              'NPK': u'N\xe1dej pre kazd\xe9ho',
              'USP': u'Uspanteco',
              'DN1933': u'Dette er Biblen p\xe5 dansk',
              'HTB': u'Het Boek',
              'REIMER': u'Reimer 2001',
              'MAORI': u'Maori Bible',
              'YLT': u"Young's Literal Translation",
              'ASV': u'American Standard Version',
              'NKJV': u'New King James Version',
              'DARBY': u'Darby Translation',
              'WE': u'Worldwide English (New Testament)',
              'TNIV': u"Today's New International Version",
              'CEV': u'Contemporary English Version',
              'KJV': u'King James Version',
              'NIVUK': u'New International Version - UK',
              'WYC': u'Wycliffe New Testament',
              'NLT': u'New Living Translation',
              'SVL': u'Levande Bibeln',
              'SV1917': u'Svenska 1917',
              'CKW': u'Cakchiquel Occidental',
              'SNC': u'Slovo na cestu',
              'LB': u'Levande Bibeln',
              'DNB1930': u'Det Norsk Bibelselskap 1930',
              'MVJ': u'Mam de Todos Santos Chuchumat\xe1n',
              'RVR1960': u'Reina-Valera 1960',
              'RVA': u'Reina-Valera Antigua',
              'LBLA': u'La Biblia de las Am\xe9ricas',
              'NVI': u'Nueva Versi\xf3n Internacional',
              'CST': u'Castilian',
              'LUTH1545': u'Luther Bibel 1545'}

    errors = [u'God did not like that.',
              u"Watch it, you're just pissing God off now."]

    def response(self, nick, args, kwargs):
        list_bibles, query, book = args
        try:
            if list_bibles:
                return self.list_bibles()
            else:
                response = self.lookup_verse(query, book)
        except Exception, error:
            log.warn('error in module %s' % self.__module__)
            log.exception(error)
            response = choice(self.errors)
        return u'%s: %s' % (nick, response)

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

        return stripHTML(res).strip()


if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)

