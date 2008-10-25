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

class SilcPlugin(madcow.Madcow, silc.SilcClient):

    def __init__(self, config, prefix):
        self.colorlib = ColorLib('mirc')
        madcow.Madcow.__init__(self, config, prefix)
        keys = silc.create_key_pair('silc.pub', 'silc.priv', passphrase='')
        nick = self.config.silcplugin.nick
        silc.SilcClient.__init__(self, keys, nick, nick, nick)
        self.channels = self._delim.split(self.config.silcplugin.channels)

        # throttling
        self.delay = self.config.irc.delay / float(1000)
        self.last_response = 0.0

    def botname(self):
        return self.config.silcplugin.nick

    def connect(self):
        log.info('connecting to %s:%s' % (self.config.silcplugin.host,
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
                log.error('exception caught in silc loop')
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
            req.channel = 'privmsg'
        else:
            req.addressed = False
            req.sendto = channel
            req.channel = channel.channel_name

        req.message = self.colorlib.strip_color(req.message)
        self.check_addressing(req)

        if req.message.startswith('^'):
            req.message = req.message[1:]
            req.colorize = True
        else:
            req.colorize = False

        self.process_message(req)

    # maybe this works better now.. XXX
    # not much of a point recovering from a kick when the silc code
    # just segfaults on you :/
    #def notify_kicked(self, kicked, reason, kicker, channel):
    #  print 'SILC: Notify (Kick):', kicked, reason, kicker, channel

    def connected(self):
        log.info('* Connected')
        for channel in self.channels:
            self.command_call('JOIN %s' % channel)

    def disconnected(self, msg):
        log.warn('* Disconnected: %s' % msg)
        if self.config.silcplugin.reconnect:
            time.sleep(self.config.silcplugin.reconnectWait)
            self.connect()

    def protocol_output(self, message, req=None):
        if not message:
            return

        # XXX is this necessary now that main bot encodes to latin1/utf8?
        # BB: Yup, still needed :)
        # CJ: your mom.
        # CJ: PS this makes no damn sense actually.  You don't send
        # decoded unicode objects to a socket.  wtf?  at some point it's
        # going to get encoded into raw bytes anyway.  i suspect it's
        # doing that encoding internally and totally disregarding our
        # wishes in what character set it uses
        message = message.decode(self.config.main.charset, 'ignore')

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
            callback(sendto, line)
            self.last_response = unix_time()

    def send_to_channel(self, channel, message):
        self._privmsg(self.send_channel_message, channel, message)

    def send_to_user(self, user, message):
        self._privmsg(self.send_private_message, user, message)


ProtocolHandler = SilcPlugin
