from madcow import Madcow, Request
import os
import re
from twisted.protocols import oscar
from twisted.internet import protocol, reactor
from include import utils
import logging as log


class AIMProtocol(Madcow):

    def __init__(self, config=None, dir=None):
        Madcow.__init__(self, config=config, dir=dir)
        self.newline = re.compile('[\r\n]+')

    def start(self):
        Madcow.start(self)
        log.info('[AIM] Logging into aol.com')
        p = protocol.ClientCreator(
            reactor, OSCARAuth, self.config.aim.username,
            self.config.aim.password, icq=0)
        p.connectTCP('login.oscar.aol.com', 5190)
        log.info('[AIM] Connected')
        p.protocolClass.BOSClass._ProtocolHandler = self
        reactor.run()

    def output(self, response, req=None):
        # override queueing system, because twisted kinda blows :(
        # encode output, lock threads, and call protocol_output
        try:
            self.lock.acquire()
            response = self.encode(response)
            self.protocol_output(response, req)
        except Exception, e:
            log.error('error in output: %s' % repr(response))
            log.exception(e)
        try:
            self.lock.release()
        except:
            pass

    def protocol_output(self, message, req=None):
        message = self.newline.sub('<br>', message)
        req.aim.sendMessage(req.nick, message)


class OSCARConnection(oscar.BOSConnection):

    capabilities = [oscar.CAP_CHAT]

    def initDone(self):
        log.info('[AIM] Initialization finished')
        self.requestSelfInfo().addCallback(self.gotSelfInfo)
        self.requestSSI().addCallback(self.gotBuddyList)

    def gotSelfInfo(self, user):
        self.name = user.name

    def gotBuddyList(self, l):
        log.info('[AIM] Retreiving buddy list')
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
        log.info('[AIM] <%s> %s' % (req.nick, req.message))
        handler.checkAddressing(req)
        handler.process_message(req)


class OSCARAuth(oscar.OscarAuthenticator):
    BOSClass = OSCARConnection


class ProtocolHandler(AIMProtocol):
    pass


