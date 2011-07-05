"""Track users on steam"""

from madcow.util import Module, strip_html
import re
from madcow.util.http import geturl, getsoup
from urlparse import urljoin
from madcow.conf import settings

class Main(Module):

    pattern = re.compile(r'^\s*(?:eyegore|steam)\s*$')
    help = 'steam - track people in community'
    status_re = re.compile(r'friendBlock_(online|in-game)')
    next_re = re.compile(re.escape(r'&gt;&gt;'), re.I)

    def init(self):
        if not settings.STEAM_GROUP:
            raise ValueError('no steam group set')
        self.group_url = 'http://steamcommunity.com/groups/%s/members' % settings.STEAM_GROUP

    def response(self, nick, args, kwargs):
        page = 1
        players = []
        while page:
            url = self.group_url + '?p=%d' % page
            soup = getsoup(url)
            next = soup.body.find('div', 'pageLinks').find(text=self.next_re)
            if next is None:
                page = None
            else:
                page = int(next.parent['href'].split('=', 1)[-1])
            for player in soup.body('div', attrs={'class': self.status_re}):
                name = strip_html(player.p.a.renderContents())
                game = player.find('span', 'linkFriend_in-game')
                if game is None:
                    if settings.STEAM_SHOW_ONLINE:
                        status = 'Online'
                    else:
                        status = None
                else:
                    status = strip_html(game.renderContents()).split('\n')[-1].replace(' - Join', '')
                if status:
                    players.append('%s: %s' % (name, status))
        if players:
            return u'\n'.join(players)
        return u'No one online.'
