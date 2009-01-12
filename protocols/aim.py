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
from include.colorlib import ColorLib
from include.utils import stripHTML
from madcow import Madcow, Request
from time import sleep
import logging as log
import time
import re

class AIMProtocol(Madcow):

    newline = re.compile(r'[\r\n]+')

    def __init__(self, config, prefix):
        self.colorlib = ColorLib(u'mirc')
        Madcow.__init__(self, config, prefix)

    def run(self):
        log.info(u'[AIM] Logging into aol.com')
        username = self.config.aim.username
        password = self.config.aim.password
        auth = OSCARAuth(username, password)
        auth.bot = self
        auth.start()
        while auth.connected:
            sleep(1)
        log.info(u'[AIM] Connected to service')
        while auth.proto.connected:
            sleep(1)
        log.info(u'[AIM] Connection closed')

    def output(self, response, req=None):
        self.handle_response(response, req)

    def protocol_output(self, message, req=None):
        print 'RESPONSE: %s' % repr(message)
        message = self.newline.sub(u'<br>', message)
        message = message.encode(self.config.main.charset, 'replace')
        req.aim.sendMessage(req.nick, message)


class ProtocolHandler(AIMProtocol):

    pass


class OSCARConnection(BOSConnection):

    capabilities = [CAP_CHAT]

    def initDone(self):
        log.info(u'[AIM] Initialization finished')
        self.requestSelfInfo()
        self.requestSSI()
        log.info(u'[AIM] Retreiving buddy list')
        self.activateSSI()
        self.setProfile(self.bot.config.aim.profile)
        self.setIdleTime(0)
        self.clientReady()
        log.info(u'[AIM] Client ready')

    def receiveMessage(self, user, multiparts, flags):
        message = multiparts[0][0]
        message = message.decode(self.bot.config.main.charset, 'replace')
        message = stripHTML(message)
        req = Request(message=message)
        req.nick = user.name
        req.channel = u'AIM'
        req.private = True
        req.addressed = True
        req.aim = self
        log.info(u'[AIM] <%s> %s' % (req.nick, req.message))
        self.bot.check_addressing(req)
        self.bot.process_message(req)


class OSCARAuth(OscarAuthenticator):

    BOSClass = OSCARConnection

