from madcow import Madcow, Request
import os
import re
from twisted.protocols import oscar
from twisted.internet import protocol, reactor
from include import utils
from logging import DEBUG, INFO, WARN, ERROR, CRITICAL


class AIMProtocol(Madcow):

    def __init__(self, config=None, dir=None):
        self.allowThreading = False
        Madcow.__init__(self, config=config, dir=dir)
        self.newline = re.compile('[\r\n]+')

    def start(self):
        self.status('[AIM] Logging into aol.com', INFO)
        server = ('login.oscar.aol.com', 5190)
        p = protocol.ClientCreator(
            reactor, OSCARAuth, self.config.aim.username, self.config.aim.password, icq = 0
        )
        p.connectTCP(*server)
        self.status('[AIM] Connected')

        p.protocolClass.BOSClass._ProtocolHandler = self
        reactor.run()

    def output(self, message, req):
        message = self.newline.sub('<br>', message)
        req.aim.sendMessage(req.nick, message)


class OSCARConnection(oscar.BOSConnection):

    capabilities = [oscar.CAP_CHAT]

    def initDone(self):
        self._ProtocolHandler.status('[AIM] Initialization finished', INFO)
        self.requestSelfInfo().addCallback(self.gotSelfInfo)
        self.requestSSI().addCallback(self.gotBuddyList)

    def gotSelfInfo(self, user):
        self.name = user.name

    def gotBuddyList(self, l):
        self._ProtocolHandler.status('[AIM] Retreiving buddy list', INFO)
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
        handler.status('[AIM] <%s> %s' % (req.nick, req.message), INFO)
        handler.checkAddressing(req)
        handler.processMessage(req)


class OSCARAuth(oscar.OscarAuthenticator):
    BOSClass = OSCARConnection


class ProtocolHandler(AIMProtocol):
    pass


