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

from twisted.internet import protocol, reactor
from twisted.words.protocols import oscar
from madcow.util import strip_html, get_logger
from madcow.util.textenc import *
from madcow import Madcow, Request
from time import sleep
import textwrap
import re
from madcow.conf import settings

#COLOR_SCHEME = 'html'
COLOR_SCHEME = None

newline_re = re.compile(r'[\r\n]+')

class AIMProtocol(Madcow):

    """Madcow AIM protocol"""

    server = ('login.oscar.aol.com', 5190)

    #black_fmt = '<div style="background-color:black;">%s</div>'
    tag_re = re.compile(r'(<(\S+?).*?>.*?</\2>)', re.DOTALL)
    whitespace_re = re.compile(r'(\s+)')

    def __init__(self, base):
        super(AIMProtocol, self).__init__(base, scheme=COLOR_SCHEME)

    def run(self):
        """Log in to AOL's servers and enter main event loop"""
        self.log.info(u'[AIM] Logging into aol.com')
        p = protocol.ClientCreator(reactor, OSCARAuth,
                                   settings.AIM_USERNAME,
                                   settings.AIM_PASSWORD, icq=0)
        p.connectTCP(*self.server)
        self.log.info('[AIM] Connected')
        p.protocolClass.BOSClass.bot = self
        reactor.callInThread(self.poll)
        reactor.run()
        self.log.info(u'[AIM] Connection closed')

    def botname(self):
        """Name used for addressing purposes"""
        return settings.AIM_USERNAME

    def protocol_output(self, message, req=None):
        """This is how we send shit to AOL.. what a mess"""
        try:
            # so, utf16 doubles the size of the FLAP packets, which
            # really limits our max message size.  if none of the ordinals
            # are outside the 7bit ascii range, convert to ascii bytes
            if not any(map(lambda ch: ord(ch) > 127, message)):
                message = encode(message, 'ascii')

            # i don't know what's going on here anymore.. let's try something
            # completely different!
            message = message.replace('&', '&amp;')
            message = message.replace('<', '&lt;')
            message = message.replace('>', '&gt;')
            message = newline_re.sub('<br>', message)

            # AIM reacts indignantly to overlong messages, so we need to
            # wrap.  try not to break up html tags injected by colorlib.
            if not hasattr(req, 'chat'):
                req.chat = None
            if not hasattr(req, 'aim'):
                req.aim = self.oscar_connection

            if req.chat:
                width = 2048
                func = req.chat.sendMessage
            else:
                width = 2545  # longer than chatrooms, who knows...
                func = req.aim.sendMessage

            # unicode stuff takes two bytes due to shitty utf-16
            if isinstance(message, unicode):
                width = int(width / 2) - 1

            for line in self.xmlwrap(message, width):
                args = [line]
                if not req.chat:
                    if not req.nick:
                        req.nick = req.sendto
                    args.insert(0, req.nick)
                reactor.callFromThread(func, *args)

                # don't spam ourselves off the server
                sleep(1)

        except Exception, error:
            self.log.exception(error)

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
        self.bot.oscar_connection = self
        self.bot.log.info(u'[AIM] Initialization finished')
        self.requestSelfInfo()
        self.requestSSI()
        self.bot.log.info(u'[AIM] Retreiving buddy list')
        self.activateSSI()
        self.setProfile(settings.AIM_PROFILE)
        self.setIdleTime(0)
        self.clientReady()
        self.bot.log.info(u'[AIM] Client ready')

    def receiveChatInvite(self, user, message, exchange, fullName, instance,
                          shortName, inviteTime):
        """Someone invited us to a chat room :("""
        self.bot.log.info(u'[AIM] Invited to chat %s by %s' % (shortName, user.name))
        if settings.AIM_AUTOJOIN_CHAT:
            self.bot.log.info(u'[AIM] Accepting chat invite')
            self.joinChat(exchange, fullName, instance)

    def receiveMessage(self, user, multiparts, flags):
        """ICBM received from someone"""
        output = []
        for part in multiparts:
            message = part[0]
            if 'unicode' in part[1:]:
                message = decode(message, 'utf-16-be')  # :(
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
        message = strip_html(message)
        req = Request(message=message)
        req.nick = user.name
        req.channel = u'AIM'
        req.aim = self
        req.private = private
        req.addressed = addressed
        req.chat = chat
        self.bot.log.info(u'[AIM] <%s> %s' % (req.nick, req.message))
        self.bot.check_addressing(req)
        self.bot.process_message(req)


OSCARAuth = oscar.OscarAuthenticator
OSCARAuth.BOSClass = OSCARConnection

class ProtocolHandler(AIMProtocol):

    allow_detach = True
