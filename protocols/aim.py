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
        self.bot.checkAddressing(req)
        self.bot.process_message(req)


class OSCARAuth(OscarAuthenticator):
    BOSClass = OSCARConnection
