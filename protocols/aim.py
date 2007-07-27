from madcow import Madcow, Request
import os
import re
from twisted.protocols import oscar
from twisted.internet import protocol, reactor
from include import utils
import logging


class AIMProtocol(Madcow):

    def __init__(self, config=None, dir=None):
        self.allowThreading = False
        Madcow.__init__(self, config=config, dir=dir)
        self.newline = re.compile('[\r\n]+')

    def start(self):
        logging.info('[AIM] Logging into aol.com')
        server = ('login.oscar.aol.com', 5190)
        p = protocol.ClientCreator(
            reactor, OSCARAuth, self.config.aim.username, self.config.aim.password, icq = 0
        )
        p.connectTCP(*server)
        logging.info('[AIM] Connected')

        p.protocolClass.BOSClass._ProtocolHandler = self
        reactor.run()

    def output(self, message, req):
        message = self.newline.sub('<br>', message)
        req.aim.sendMessage(req.nick, message)


class OSCARConnection(oscar.BOSConnection):

    capabilities = [oscar.CAP_CHAT]

    def initDone(self):
        logging.info('[AIM] Initialization finished')
        self.requestSelfInfo().addCallback(self.gotSelfInfo)
        self.requestSSI().addCallback(self.gotBuddyList)

    def gotSelfInfo(self, user):
        self.name = user.name

    def gotBuddyList(self, l):
        logging.info('[AIM] Retreiving buddy list')
        self.activateSSI()
        self.setProfile(self._ProtocolHandler.config.aim.profile)
        self.setIdleTime(0)
        self.clientReady()

    def receiveMessage(self, user, multiparts, flags):
        req = Request(message=utils.stripHTML(multiparts[0][0]))
        req.nick = user.name
        req.channel = 'AIM'
        req.private = True
        req.addressed = True
        req.aim = self

        handler = self._ProtocolHandler
        logging.info('[AIM] <%s> %s' % (req.nick, req.message))
        handler.checkAddressing(req)
        handler.processMessage(req)


class OSCARAuth(oscar.OscarAuthenticator):
    BOSClass = OSCARConnection


class ProtocolHandler(AIMProtocol):
    pass


