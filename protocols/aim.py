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

from include.colorlib import ColorLib
from include.utils import stripHTML
from madcow import Madcow, Request
from time import sleep
import logging as log
import re
from include.twisted.words.protocols import oscar
from include.twisted.internet import protocol, reactor
import random

# max message sizes before the aol services gets angry.
# note: unicode messages are utf-16 so thus use two bytes per character
#
# direct message:
#
# *** SENDING 2545 BYTE MESSAGE ***
# *** SENDING 2607 BYTE FLAP ***
#
# chat room:
#
# *** TESTING SPAM WITH 1024 CHARS ***
# *** SENDING 2111 BYTE FLAP ***

class AIMProtocol(Madcow):

    newline = re.compile(r'[\r\n]+')
    server = ('login.oscar.aol.com', 5190)
    color_fmt = '<div style="background-color:black;color:white;">%s</div>'

    def __init__(self, config, prefix):
        self.colorlib = ColorLib(u'html')
        Madcow.__init__(self, config, prefix)

    def run(self):
        log.info(u'[AIM] Logging into aol.com')
        p = protocol.ClientCreator(reactor, OSCARAuth,
                                   self.config.aim.username,
                                   self.config.aim.password, icq=0)
        p.connectTCP(*self.server)
        log.info('[AIM] Connected')
        p.protocolClass.BOSClass.bot = self

        reactor.callInThread(self.poll)
        reactor.run()
        log.info(u'[AIM] Connection closed')

    def botname(self):
        return self.config.aim.username

    def protocol_output(self, message, req=None):
        try:
            if req.colorize:
                # color output if requested
                style = random.choice(self.colorlib._rainbow_map.keys())
                message = self.colorlib.rainbow(message, style=style)
                message = self.color_fmt % message
            args = [self.newline.sub(u'<br>', message)]
            if req.chat:
                func = req.chat.sendMessage
            else:
                func = req.aim.sendMessage
                args.insert(0, req.nick)
            log.debug('OUT: %s' % repr(args))
            reactor.callFromThread(func, *args)
        except Exception, error:
            pass

    def poll(self):
        while self.running:
            self.check_response_queue()
            sleep(0.5)

    @classmethod
    def xmlwrap(cls, message, length):
        """Wraps a message based on max length without breaking html tags"""


class ProtocolHandler(AIMProtocol):

    pass


class OSCARConnection(oscar.BOSConnection):

    capabilities = [oscar.CAP_CHAT]

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

    def receiveChatInvite(self, user, message, exchange, fullName, instance,
                          shortName, inviteTime):
        log.info(u'[AIM] Invited to chat %s by %s' % (shortName, user.name))
        if self.bot.config.aim.autojoin:
            log.info(u'[AIM] Accepting chat invite')
            self.joinChat(exchange, fullName, instance)

    def receiveMessage(self, user, multiparts, flags):
        output = []
        for part in multiparts:
            message = part[0]
            if 'unicode' in part[1:]:
                message = message.decode('utf-16-be')  # :(
            output.append(message)
        message = u' '.join(output)
        self.on_message(user, message, True, True)

    def chatReceiveMessage(self, chat, user, message):
        self.on_message(user, message, False, False, chat)

    def on_message(self, user, message, private, addressed, chat=None):
        if user.name == self.bot.botname():
            return
        message = stripHTML(message)
        req = Request(message=message)

        # lines that start with ^ will have their output rainbowed
        if req.message.startswith(u'^'):
            req.message = req.message[1:]
            req.colorize = True
        else:
            req.colorize = False

        req.nick = user.name
        req.channel = u'AIM'
        req.aim = self
        req.private = private
        req.addressed = addressed
        req.chat = chat
        log.info(u'[AIM] <%s> %s' % (req.nick, req.message))
        self.bot.check_addressing(req)
        self.bot.process_message(req)


class OSCARAuth(oscar.OscarAuthenticator):

    BOSClass = OSCARConnection
