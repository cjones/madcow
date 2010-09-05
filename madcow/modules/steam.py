"""Track users on steam"""

from madcow.util import Module
import re
from madcow.util.http import geturl
from urlparse import urljoin

class Main(Module):

    pattern = re.compile(r'^\s*(?:eyegore|steam)\s*$')
    help = 'steam - track people in community'
    base_url = 'http://steamcommunity.com/'
    base_group_url = urljoin(base_url, 'groups/')
    member_re = re.compile(r'rgGroupMembers\[\'\[(.*?)\]\'\]\s+=\s+new\s+Arra'
                           r'y\("(.*?)",\s+"(.*?)"')
    link_re = re.compile(r'<a\s+class="groupMemberLink"\s+id="member_\[(.*?)'
                         r'\]"\s+href="(.*?)">')
    game_re = re.compile(r'<p\s+id="statusInGameText">(.*?)</p>', re.DOTALL)

    def init(self):
        if not settings.STEAM_GROUP:
            raise ValueError('no steam group set')
        self.group_url = urljoin(self.base_group_url, settings.STEAM_GROUP)

    def response(self, nick, args, kwargs):
        group_page = geturl(self.group_url)
        ids = {}
        for id, name, status in self.member_re.findall(group_page):
            ids[id] = dict(name=name, status=status)
        for id, link in self.link_re.findall(group_page):
            ids[id]['link'] = link
        ingame = []
        online = []
        for data in ids.values():
            if data['status'] == 'In-Game':
                page = geturl(data['link'])
                try:
                    game = self.game_re.search(page).group(1).strip()
                except AttributeError:
                    game = 'Non-Steam Game'
                ingame.append('%s: %s' % (data['name'], game))
            elif data['status'] == 'Online' and settings.STEAM_SHOW_ONLINE:
                online.append('%s: Online' % data['name'])
        output = ingame + online
        if not output:
            if settings.STEAM_SHOW_ONLINE:
                message = 'Online'
            else:
                message = 'In-Game'
            output = ['No users ' + message]
        return '\n'.join(output)
