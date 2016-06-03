"""Predicted Electoral Vote Count"""

import re
from madcow.util.http import getsoup
from madcow.util.color import ColorLib
from madcow.util import Module, strip_html

class Main(Module):

    pattern = re.compile(r'^\s*(election|ev)\s*$', re.I)
    help = u'ev - current election 2008 vote prediction'
    baseurl = u'http://www.electoral-vote.com/'

    def init(self):
        if self.madcow is None:
            self.colorlib = ColorLib('ansi')
        else:
            self.colorlib = self.madcow.colorlib

    def colorize(self, color, key, val):
        return u'%s: %s' % (key, val)

    def render(self, node):
        pass

    def response(self, nick, args, kwargs):
        soup = getsoup(self.baseurl)
        out = []
        for box in soup.find('div', 'score-box').findAll('div', 'box'):
            score = []
            for key in 'name', 'score':
                val = strip_html(box.find('span', key).renderContents()).replace(u'\xa0', u'').strip()
                if key == 'name':
                    if val == u'Obama':
                        color = 'blue'
                    elif val == 'Romney':
                        color = 'red'
                    else:
                        color = None
                    if color:
                        val = self.colorlib.get_color(color, text=val)
                if val:
                    score.append(val)
            if score:
                out.append(u'%s: %s' % tuple(score))
        return u'%s: %s' % (nick, u', '.join(out))
        #from IPython.Shell import IPShellEmbed as S; #S()()
