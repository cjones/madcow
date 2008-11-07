# Copyright (C) 2007, 2008 Bryan Burns and Christopher Jones
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
#
#  silc.py
#  madcow
#
#  Created by Bryan Burns on 2007-06-19.
#
# Confirmed to work with pysilc0.4 and silc-toolkit 1.0.2
#
# UPDATE: confirmed to work with pysilc-0.5 and silc-toolkit-1.1.8

import madcow
import silc
import time
import re
from include.colorlib import ColorLib
import logging as log
from time import sleep, time as unix_time
from include import encoding

class SilcPlugin(madcow.Madcow, silc.SilcClient):

    def __init__(self, config, prefix):
        self.colorlib = ColorLib(u'mirc')
        madcow.Madcow.__init__(self, config, prefix)
        keys = silc.create_key_pair('silc.pub', 'silc.priv', passphrase='')
        nick = self.config.silcplugin.nick
        silc.SilcClient.__init__(self, keys, nick, nick, nick)
        self.channels = self._delim.split(self.config.silcplugin.channels)

        # throttling
        self.delay = self.config.silcplugin.delay / float(1000)
        self.last_response = 0.0

    def botname(self):
        return self.config.silcplugin.nick

    def connect(self):
        log.info(u'connecting to %s:%s' % (self.config.silcplugin.host,
                                          self.config.silcplugin.port))
        self.connect_to_server(self.config.silcplugin.host,
                               self.config.silcplugin.port)

    def run(self):
        self.run_one()  # hack to work with new silc
        self.connect()
        while self.running:
            self.check_response_queue()
            try:
                self.run_one()
            except KeyboardInterrupt:
                self.running = False
                break
            except Exception, error:
                log.error(u'exception caught in silc loop')
                log.exception(error)
            time.sleep(0.2)

    def private_message(self, sender, flags, message):
        self.on_message(sender, None, flags, message, True)

    def channel_message(self, sender, channel, flags, message):
        self.on_message(sender, channel, flags, message, False)

    def on_message(self, sender, channel, flags, message, private):
        req = madcow.Request(message=message)
        req.nick = sender.nickname
        req.private = private
        req.silc_sender = sender
        if private:
            req.addressed = True
            req.sendto = sender
            req.channel = u'privmsg'
        else:
            req.addressed = False
            req.sendto = channel
            req.channel = channel.channel_name

        req.message = req.message.decode(encoding.detect(req.message),
                                         'replace')
        req.message = self.colorlib.strip_color(req.message)
        self.check_addressing(req)

        if req.message.startswith(u'^'):
            req.message = req.message[1:]
            req.colorize = True
        else:
            req.colorize = False

        self.process_message(req)

    # maybe this works better now.. XXX
    # not much of a point recovering from a kick when the silc code
    # just segfaults on you :/
    #def notify_kicked(self, kicked, reason, kicker, channel):
    #  print u'SILC: Notify (Kick):', kicked, reason, kicker, channel

    def connected(self):
        log.info(u'* Connected')
        for channel in self.channels:
            self.command_call(u'JOIN %s' % channel)

    def disconnected(self, msg):
        log.warn(u'* Disconnected: %s' % msg)
        if self.config.silcplugin.reconnect:
            time.sleep(self.config.silcplugin.reconnectWait)
            self.connect()

    def protocol_output(self, message, req=None):
        if not message:
            return

        if req.colorize:
            message = self.colorlib.rainbow(message)
        if req.private:
            self.send_to_user(req.sendto, message)
        else:
            self.send_to_channel(req.sendto, message)

    # should these use irc's textwrap?
    # Nah, silc doesn't have message limits like IRC, so wrapping just
    # induces unnecessary ugliness

    def _privmsg(self, callback, sendto, message):
        for line in message.splitlines():
            delta = unix_time() - self.last_response
            if delta < self.delay:
                sleep(self.delay - delta)

            # XXX i guess pysilc expects unicode.. so, no control over
            # what the encoding is, sadly... silc FTL
            #line = line.encode(self.charset, 'replace')

            callback(sendto, line)
            self.last_response = unix_time()

    def send_to_channel(self, channel, message):
        self._privmsg(self.send_channel_message, channel, message)

    def send_to_user(self, user, message):
        self._privmsg(self.send_private_message, user, message)


ProtocolHandler = SilcPlugin
