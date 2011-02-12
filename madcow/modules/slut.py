"""
Slutcheck - Uses google "safesearch" to determine how "slutty" a word or
phrase is.  (To get an accurate slut rating for a phrase it should be
quoted.)

Uses the ratio of hits doing an unsafe search to the number of hits
doing a safe search to determine the score.  If a safe search returns 0
results, and unsafe returns, say, 100, the phrase is 100% slutty.  If
the number of results for both are equal, the phrase is 0% slutty.
"""

import re
from madcow.util import Module
from madcow.util.http import geturl
from urlparse import urljoin

match_re = re.compile(r'About ([\d,]+) results')
filter_re = re.compile(r'The word <b>"(\w+)"</b> has been filtered from the search')
baseURL = u'http://www.google.com/'
searchURL = urljoin(baseURL, u'/search')

class WordFiltered(Exception):

    """Indicates a word has been filtered by google safe search"""

    def __init__(self, word):
        self.word = word

    def __str__(self):
        return repr(self.word)


def cleanurl(url):
    return url.replace(u" ", u"+")


def slutrating(phrase):

    phrase = cleanurl(phrase)

    try:
        data = geturl(searchURL, opts={u'q': phrase, u'safe': u'off'})
        unsafe = int(match_re.search(data).group(1).replace(u',', u''))
    except AttributeError:
        unsafe = 0

    try:
        data = geturl(searchURL, opts={u'q': phrase, u'safe': u'active'})
        try:
            filtered = filter_re.search(data).group(1)
            raise WordFiltered(filtered)
        except AttributeError:
            pass
        safe = int(match_re.search(data).group(1).replace(u',', u''))
    except AttributeError:
        safe = 0

    value = float(unsafe - safe) / float(unsafe)
    if value < 0:
        value = 0
    return value


class Main(Module):

    enabled = True
    pattern = re.compile(u'^\s*slutcheck\s+(.+)')
    require_addressing = True
    help = u"slutcheck <phrase> - see how slutty the phrase is"
    error = u'I failed to perform that lookup'

    def response(self, nick, args, kwargs):
        try:
            query = u" ".join(args)
            rating = slutrating(query)
            return u"%s is %.2f%% slutty." % (query, rating * 100)
        except TypeError, error:
            self.log.exception('what')
            return u"%s: Sorry, google isn't being cooperative.." % nick
        except WordFiltered, error:
            return u"%s: Hmm, google is filtering the word '%s'.. 100%% slutty!" % (nick, error.word)
