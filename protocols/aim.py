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

from include.twisted.internet import protocol, reactor
from include.twisted.words.protocols import oscar
from include.colorlib import ColorLib
from include.utils import stripHTML
from madcow import Madcow, Request
from time import sleep
import logging as log
import random
import re

class AIMProtocol(Madcow):

    """Madcow AIM protocol"""

    server = ('login.oscar.aol.com', 5190)

    #black_fmt = '<div style="background-color:black;">%s</div>'
    tag_re = re.compile(r'(<(\S+?).*?>.*?</\2>)', re.DOTALL)
    whitespace_re = re.compile(r'(\s+)')

    def __init__(self, config, prefix):
        self.colorlib = ColorLib(u'html')
        Madcow.__init__(self, config, prefix)

    def run(self):
        """Log in to AOL's servers and enter main event loop"""
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
        """Name used for addressing purposes"""
        return self.config.aim.username

    def protocol_output(self, message, req=None):
        """This is how we send shit to AOL"""
        try:
            # so, utf16 doubles the size of the FLAP packets, which
            # really limits our max message size.  if none of the ordinals
            # are outside the 7bit ascii range, convert to ascii bytes
            if not [ch for ch in message if ord(ch) > 127]:
                message = message.encode('us-ascii')

            # escape stuff so it's not all like LOL HTML
            message = oscar.html(message)

            # color output if requested
            #if req.colorize:
            #    style = random.choice(self.colorlib._rainbow_map.keys())
            #    message = self.colorlib.rainbow(message, style=style)

            # AIM reacts indignantly to overlong messages, so we need to
            # wrap.  try not to break up html tags injected by colorlib.
            if req.chat:
                width = 2048
                func = req.chat.sendMessage
            else:
                width = 2545  # longer than chatrooms, who knows...
                func = req.aim.sendMessage

            # unicode stuff takes two bytes due to shitty utf-16
            if isinstance(message, unicode):
                width = int(width / 2) - 1

            # make room for the div tag that sets a black background
            #if req.colorize:
            #    width -= 43

            # XXX this regex does really really bad things with lots of color
            for line in self.xmlwrap(message, width):

                #if req.colorize:
                #    line = self.black_fmt % line

                args = [line]
                if not req.chat:
                    args.insert(0, req.nick)
                reactor.callFromThread(func, *args)

                # don't spam ourselves off the server
                sleep(1)

        except Exception, error:
            log.exception(error)

    def poll(self):
        """This thread looks for responses and dispatches them to clients"""
        while self.running and reactor._started and not reactor._stopped:
            self.check_response_queue()
            sleep(0.5)

    @classmethod
    def xmlwrap(cls, message, width):
        """Wraps a message based on max length without breaking html tags"""
        parts = []
        tag = None
        for part in cls.tag_re.split(message):
            if not part or part == tag:
                continue
            try:
                tag = cls.tag_re.search(part).group(2)
                parts.append(part)
            except AttributeError:
                tag = None
                parts += cls.whitespace_re.split(part)

        lines = [[]]
        size = 0
        for part in parts:
            if part:
                part_len = len(part)
                if size and size + part_len > width:
                    lines.append([])
                    size = 0
                lines[-1].append(part)
                size += part_len
        return [''.join(parts) for parts in lines]


class OSCARConnection(oscar.BOSConnection):

    """Protocol handler for AIM"""

    capabilities = [oscar.CAP_CHAT]

    def initDone(self):
        """After auth, we need to set a few things up"""
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
        """Someone invited us to a chat room :("""
        log.info(u'[AIM] Invited to chat %s by %s' % (shortName, user.name))
        if self.bot.config.aim.autojoin:
            log.info(u'[AIM] Accepting chat invite')
            self.joinChat(exchange, fullName, instance)

    def receiveMessage(self, user, multiparts, flags):
        """ICBM received from someone"""
        output = []
        for part in multiparts:
            message = part[0]
            if 'unicode' in part[1:]:
                message = message.decode('utf-16-be')  # :(
            output.append(message)
        message = u' '.join(output)
        self.on_message(user, message, True, True)

    def chatReceiveMessage(self, chat, user, message):
        """Someone speaketh on a chatroom"""
        self.on_message(user, message, False, False, chat)

    def on_message(self, user, message, private, addressed, chat=None):
        """Process incoming messages and dispatch to main bot"""
        if user.name == self.bot.botname():
            return
        message = stripHTML(message)
        req = Request(message=message)

        # lines that start with ^ will have their output rainbowed
        #if req.message.startswith(u'^'):
        #    req.message = req.message[1:]
        #    req.colorize = True
        #else:
        #    req.colorize = False

        req.nick = user.name
        req.channel = u'AIM'
        req.aim = self
        req.private = private
        req.addressed = addressed
        req.chat = chat
        log.info(u'[AIM] <%s> %s' % (req.nick, req.message))
        self.bot.check_addressing(req)
        self.bot.process_message(req)


ProtocolHandler = AIMProtocol
OSCARAuth = oscar.OscarAuthenticator
OSCARAuth.BOSClass = OSCARConnection
