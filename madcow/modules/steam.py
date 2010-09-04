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

"""Track users on steam"""

from include.utils import Module
import logging as log
import re
from include.useragent import geturl
from urlparse import urljoin

__version__ = u'0.1'
__author__ = u'Chris Jones <cjones@gruntle.org>'
__all__ = []

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

    def __init__(self, madcow):
        if not madcow.config.steam.enabled:
            self.enabled = False
            return
        if not madcow.config.steam.group:
            self.enabled = False
            log.error('steam module enabled but no group set!')
            return
        self.online = madcow.config.steam.online
        self.group_url = urljoin(self.base_group_url,
                                 madcow.config.steam.group)


    def response(self, nick, args, kwargs):
        try:
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
                elif data['status'] == 'Online' and self.online:
                    online.append('%s: Online' % data['name'])
            output = ingame + online
            if not output:
                if self.online:
                    message = 'Online'
                else:
                    message = 'In-Game'
                output = ['No users ' + message]
            return '\n'.join(output)
        except Exception, error:
            log.warn(u'error in module %s' % self.__module__)
            log.exception(error)
            return u'%s: %s' % (nick, error)


if __name__ == u'__main__':
    from include.utils import test_module
    test_module(Main)
