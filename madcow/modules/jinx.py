# Created by Bryan Burns on 2007-07-17.
# Handle coke allocation

import time
from madcow.util import Module

class ChatLine(object):

    """Records a single line of IRC chat"""

    def __init__(self, nick, text):
        self.nick = nick
        self.text = text
        self.timestamp = time.time()

    def __str__(self):
        return u"%s: <%s> %s\n" % (unicode(self.timestamp), self.nick,
                                   self.text)


class ChatLog(object):

    """Holds chat lines for a preconfigured duration of time"""

    def __init__(self, timeout=5):
        self.timeout = timeout
        self.lines = []

    def cull(self):
        """removes any lines that are beyond the timeout."""
        now = time.time()
        self.lines = [line for line in self.lines
                      if line.timestamp + self.timeout > now]

    def getMatchingLine(self, line):
        """
        If a line exists in the log that matches the line passed in, returns
        that line object, otherwise returns None.  A line 'matches' if the text
        is the same, case insensitive and ignoring whitespace.
        """

        # easy way to ignore case and whitespace
        tokens = map(unicode.lower, line.text.split())
        for l in self.lines:
            if map(unicode.lower, l.text.split()) == tokens:
                return l  # found a match

        return None  # no matches found

    def add(self, line):
        """adds a line to the log and culls any stale lines."""
        self.cull()
        self.lines.append(line)

    def __str__(self):
        s = u""
        for line in self.lines:
            s += unicode(line)
        return s


class Main(Module):

    priority = 1
    terminate = False
    allow_threading = False
    pattern = Module._any
    require_addressing = False
    help = u'this module watches people who say the same thing within 5 seconds'

    def init(self):
        self.chatlog = ChatLog()

    def response(self, nick, args, kwargs):
        line = args[0]
        cl = ChatLine(nick, line)
        self.chatlog.add(cl)
        oldline = self.chatlog.getMatchingLine(cl)
        if oldline and oldline.nick != nick:
            return u"Jinx! %s owes %s a coke!" % (nick, oldline.nick)
