"""Infobot style karma"""

from madcow.util import Module
import re
from learn import Main as Learn

class KarmaResponse(object):

    def __init__(self, reply, matched):
        self.reply = reply
        self.matched = matched


class Karma(object):

    """Infobot style karma"""

    _adjust_pattern = re.compile(r'^\s*(.*?)[+-]([+-]+)\s*$')
    _query_pattern = re.compile(r'^\s*karma\s+(\S+)\s*\?*\s*$')
    _dbname = u'karma'

    def __init__(self, madcow):
        self.learn = Learn(madcow)

    def process(self, nick, input):
        kr = KarmaResponse(reply=None, matched=False)

        # see if someone is trying to adjust karma
        try:
            target, adjustment = Karma._adjust_pattern.search(input).groups()
            # don't let people adjust their own karma ;p
            if nick.lower() != target.lower():
                self.adjust(nick=target, adjustment=adjustment)
            kr.matched = True
        except AttributeError:
            pass

        # detect a query for someone's karma
        try:
            target = Karma._query_pattern.search(input).group(1)
            karma = self.query(nick=target)
            kr.matched = True
            kr.reply = u"%s: %s's karma is %s" % (nick, target, karma)
        except AttributeError:
            pass
        return kr

    def set(self, nick, karma):
        self.learn.set(Karma._dbname, nick.lower(), unicode(karma))

    def adjust(self, nick, adjustment):
        karma = self.query(nick)
        adjustment, size = adjustment[0], len(adjustment)
        exec(u'karma ' + adjustment + u'= size')
        self.set(nick=nick, karma=karma)

    def query(self, nick):
        karma = self.learn.lookup(Karma._dbname, nick.lower())
        if karma is None:
            karma = 0
            self.set(nick=nick, karma=karma)
        return int(karma)


class Main(Module):

    pattern = Module._any
    require_addressing = False
    help = u'\n'.join([
        u"<nick>[++/--] - adjust someone's karma",
        u"karma <nick> - see what someone's karma is",
        ])
    allow_threading = False

    def init(self):
        self.karma = Karma(self.madcow)

    def response(self, nick, args, kwargs):
        """This function should return a response to the query or None."""
        input = args[0]
        kr = self.karma.process(nick, input)
        kwargs[u'req'].matched = kr.matched
        if kr.reply:
            return unicode(kr.reply)
