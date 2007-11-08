"""Get summary from WikiPedia"""

import re
from include.wikiparse import WikiParser


class MatchObject(object):

    def __init__(self, *args, **kwargs):
        self.enabled = True
        self.pattern = re.compile('^\s*(?:wp|wiki|wikipedia)\s+(.*?)\s*$', re.I)
        self.requireAddressing = True
        self.thread = True
        self.wrap = False
        self.help = 'wiki <term> - look up summary of term on wikipedia'

    def response(self, **kwargs):
        """Return summary of WikiPedia page"""

        try:
            return WikiParser(query=kwargs['args']).summary
        except Exception, e:
            return '%s: problem with query: %s' % (kwargs['nick'], e)


