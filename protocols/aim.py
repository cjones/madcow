# Copyright (C) 2007, 2008 Christopher Jones
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

"""AIM Protocol"""

from include.oscar import BOSConnection, CAP_CHAT, OscarAuthenticator
from madcow import Madcow, Request
import re
import logging as log
import time
from include.utils import stripHTML
from time import sleep

class AIMProtocol(Madcow):

    newline = re.compile(r'[\r\n]+')

    def run(self):
        log.info('[AIM] Logging into aol.com')
        username = self.config.aim.username
        password = self.config.aim.password
        auth = OSCARAuth(username, password)
        auth.bot = self
        auth.start()
        while auth.connected:
            sleep(1)
        log.info('[AIM] Connected to service')
        while auth.proto.connected:
            sleep(1)
        log.info('[AIM] Connection closed')

    def output(self, response, req=None):
        self.handle_response(response, req)

    def protocol_output(self, message, req=None):
        message = self.newline.sub('<br>', message)
        req.aim.sendMessage(req.nick, message)


class ProtocolHandler(AIMProtocol):
    pass


class OSCARConnection(BOSConnection):
    capabilities = [CAP_CHAT]

    def initDone(self):
        log.info('[AIM] Initialization finished')
        self.requestSelfInfo()
        self.requestSSI()
        log.info('[AIM] Retreiving buddy list')
        self.activateSSI()
        self.setProfile(self.bot.config.aim.profile)
        self.setIdleTime(0)
        self.clientReady()
        log.info('[AIM] Client ready')

    def receiveMessage(self, user, multiparts, flags):
        req = Request(message=stripHTML(multiparts[0][0]))
        req.nick = user.name
        req.channel = 'AIM'
        req.private = True
        req.addressed = True
        req.aim = self
        log.info('[AIM] <%s> %s' % (req.nick, req.message))
        self.bot.check_addressing(req)
        self.bot.process_message(req)


class OSCARAuth(OscarAuthenticator):
    BOSClass = OSCARConnection
