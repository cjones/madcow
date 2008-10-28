#!/usr/bin/env python
#
# Copyright (C) 2007, 2008 Christopher Jones and Bryan Burns
#
# This file is part of Madcow.
#
# Madcow is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Madcow is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Madcow.  If not, see <http://www.gnu.org/licenses/>.
#
#  slut.py
#  madcow-1.31
#
#  Created by Bryan Burns on 2007-06-20.
#

"""
Slutcheck - Uses google "safesearch" to determine how "slutty" a word or
phrase is.  (To get an accurate slut rating for a phrase it should be
quoted.)

Uses the ratio of hits doing an unsafe search to the number of hits
doing a safe search to determine the score.  If a safe search returns 0
results, and unsafe returns, say, 100, the phrase is 100% slutty.  If
the number of results for both are equal, the phrase is 0% slutty.
"""

import urllib2
import re
from include.utils import Module
from include.useragent import geturl
import logging as log
from urlparse import urljoin

match_re = re.compile(r'Results .* of about <b>([\d,]+)</b> for')
filter_re = re.compile(
        r'The word <b>"(\w+)"</b> has been filtered from the search')
baseURL = 'http://www.google.com/'
searchURL = urljoin(baseURL, '/search')

class WordFiltered(Exception):

    """Indicates a word has been filtered by google safe search"""

    def __init__(self, word):
        self.word = word

    def __str__(self):
        return repr(self.word)


def cleanurl(url):
    return url.replace(" ", "+")


def slutrating(phrase):

    phrase = cleanurl(phrase)

    for i in range(5):  # Try up to 5 times to get a good result
        try:
            data = geturl(searchURL, opts={'q': phrase, 'safe': 'off'})
            unsafe = int(match_re.search(data).group(1).replace(',', ''))
        except AttributeError:
            unsafe = 0

        try:
            data = geturl(searchURL, opts={'q': phrase, 'safe': 'active'})
            try:
                filtered = filter_re.search(data).group(1)
                raise WordFiltered(filtered)
            except AttributeError:
                pass
            safe = int(match_re.search(data).group(1).replace(',', ''))
        except AttributeError:
            safe = 0

        if not unsafe:
            if safe > 0:
                continue # shouldn't really be possible to have safe w/o unsafe
            else:
                return 0

        value = float(unsafe - safe) / float(unsafe)
        if value > 0:
            return value


class Main(Module):

    enabled = True
    pattern = re.compile('^\s*slutcheck\s+(.+)')
    require_addressing = True
    help = "slutcheck <phrase> - see how slutty the phrase is"

    def response(self, nick, args, kwargs):
        try:
            query = " ".join(args)
            rating = slutrating(query)
            return "%s is %.2f%% slutty." % (query, rating * 100)
        except TypeError, error:
            return "%s: Sorry, google isn't being cooperative.." % nick
        except WordFiltered, error:
            return "%s: Hmm, google is filtering the word '%s'.." % (
                    nick, error.word)
        except Exception, error:
            log.warn('error in module %s' % self.__module__)
            log.exception(error)
            return '%s: I failed to perform that lookup' % nick


if __name__ == '__main__':
    from include.utils import test_module
    test_module(Main)
