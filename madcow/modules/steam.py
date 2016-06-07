"""Track users on steam"""

from madcow.util import Module, strip_html
import re
from urlparse import urljoin
from madcow.conf import settings

class Main(Module):

    pattern = re.compile(r'^\s*(?:eyegore|steam)\s*$')
    help = 'steam - track people in community'
    next_re = re.compile(re.escape(r'&gt;&gt;'), re.I)

    def init(self):
        if not settings.STEAM_GROUP:
            raise ValueError('no steam group set')
        self.group_url = 'http://steamcommunity.com/groups/%s/members' % settings.STEAM_GROUP

    def response(self, nick, args, kwargs):
        kwargs['req'].blockquoted = True
        page = 1
        players = []
        while page:
            url = self.group_url + '?p=%d' % page
            soup = self.getsoup(url)
            next = soup.body.find('div', 'pageLinks').find(text=self.next_re)
            if next is None:
                page = None
            else:
                page = int(next.parent['href'].split('=', 1)[-1])

            member_list = soup.body.find('div', id='memberList')
            members = member_list('div', {'class': re.compile(r'\bmember_block\b')})
            for member in members:
                rank_icon = member.find('div', 'rank_icon')
                if rank_icon is not None:
                    rank = rank_icon['title']
                else:
                    rank = 'Member'
                content = member.find('div', {'class': re.compile(r'\bmember_block_content\b')})
                classes = dict(content.attrs)['class'].strip().split()
                online = 'online' in classes
                offline = 'offline' in classes
                if online and not offline:
                    status = 'online'
                elif offline and not online:
                    status = 'offline'
                else:
                    status = 'unknown'
                name = content.find('a', {'class': re.compile(r'\blinkFriend\b')})
                name = name.renderContents().strip().decode('utf-8')
                line = u'{} [{}] {}'.format(name, rank, status)
                players.append(line)

        if players:
            return u'\n'.join(players)
        return u'No one online.'
