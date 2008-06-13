import textwrap
from include import irclib
import re
import sys
from madcow import Madcow, Request
from include.colorlib import ColorLib
import random
import logging as log
from time import sleep, time as unix_time

class IRCProtocol(Madcow):
    """Implements IRC protocol for madcow"""

    events = ['welcome', 'disconnect', 'kick', 'privmsg', 'pubmsg', 'namreply']

    def __init__(self, config=None, dir=None):
        Madcow.__init__(self, config=config, dir=dir)

        self.colorlib = ColorLib('mirc')
        if log.root.level <= log.DEBUG:
            irclib.DEBUG = 1
        else:
            irclib.DEBUG = 0
        self.irc = irclib.IRC()
        self.server = self.irc.server()
        for event in self.events:
            log.info('[IRC] * Registering event: %s' % event)
            self.server.add_global_handler(
                event,
                getattr(self, 'on_' + event),
                0,
            )
        if self.config.irc.channels is not None:
            self.channels = self._delim.split(self.config.irc.channels)
        else:
            self.channels = []
        self.names = {}
        self.last_names_update = unix_time()

    def connect(self):
        log.info('[IRC] * Connecting to %s:%s' % (
            self.config.irc.host, self.config.irc.port))
        self.server.connect(
            self.config.irc.host,
            self.config.irc.port,
            self.config.irc.nick
        )

    def stop(self):
        Madcow.stop(self)
        log.info('[IRC] * Quitting IRC')
        message = self.config.irc.quitMessage
        if message is None:
            message = 'no reason'
        self.server.disconnect(message)

    def run(self):
        self.connect()
        while self.running:
            try:
                self.check_response_queue()
                self.irc.process_once(0.2)
            except KeyboardInterrupt:
                self.running = False
            except Exception, e:
                log.error('Error in IRC loop')
                log.exception(e)

    def botName(self):
        return self.server.get_nickname()

    def on_welcome(self, server, event):
        """welcome event triggers startup sequence"""
        log.info('[IRC] * Connected')

        # identify with nickserv
        if self.config.irc.nickServUser and self.config.irc.nickServPass:
            self.server.privmsg(self.config.irc.nickServUser,
                    'IDENTIFY %s' % self.config.irc.nickServPass)

        # become an oper
        if self.config.irc.oper:
            log.info('[IRC] * Becoming an OPER')
            self.server.oper(self.config.irc.operUser, self.config.irc.operPass)

        # join all channels
        for channel in self.channels:
            log.info('[IRC] * Joining: %s' % channel)
            self.server.join(channel)

    def on_disconnect(self, server, event):
        """disconnected from IRC"""
        log.warn('[IRC] * Disconnected from server')
        if self.config.irc.reconnect and self.running:
            sleep(self.config.irc.reconnectWait)
            self.connect()

    def on_kick(self, server, event):
        """kicked from channel"""
        log.warn('[IRC] * Kicked from %s by %s' % (event.arguments()[0],
            event.target()))
        if event.arguments()[0].lower() == server.get_nickname().lower():
            if self.config.irc.rejoin:
                if self.config.irc.rejoinWait > 0:
                    sleep(self.config.irc.rejoinWait)
                server.join(event.target())
                server.privmsg(event.target(), self.config.irc.rejoinReply)

    def protocol_output(self, message, req=None):
        """output to IRC"""
        if message is None:
            return

        # IRC really doesn't like null characters
        message = message.replace('\x00', '')
        if not len(message):
            return

        # color output if requested
        if req.colorize:
            style = random.choice(self.colorlib._rainbow_map.keys())
            message = self.colorlib.rainbow(message, style=style)

        # MUST wrap if unset because irc will boot you for exceeding maxlen
        wrap = self.config.irc.wrapsize
        if wrap is None or wrap > 400:
            wrap = 400

        # each line gets its own privmsg
        output = []
        for line in message.splitlines():
            if len(line) > wrap:
                for wrapped in textwrap.wrap(line, wrap):
                    output.append(wrapped)
            else:
                output.append(line)

        # send to IRC socket
        for line in output:
            self.server.privmsg(req.sendTo, line)

    def on_privmsg(self, server, event):
        """private message received"""
        self.on_message(server, event, private=True)

    def on_pubmsg(self, server, event):
        """public message received"""
        self.on_message(server, event, private=False)

    def on_message(self, server, event, private):
        """process incoming messages"""
        req = Request(message=event.arguments()[0])
        req.nick = irclib.nm_to_n(event.source())
        req.channel = event.target()
        req.private = private

        if private:
            req.sendTo = req.nick
            req.addressed = True
        else:
            req.sendTo = req.channel
            req.addressed = False

        # strip control codes from incoming lines
        req.message = self.colorlib.strip_color(req.message)

        # strip adressing and set req attributes
        self.checkAddressing(req)

        # lines that start with ^ will have their output rainbowed
        if req.message.startswith('^'):
            req.message = req.message[1:]
            req.colorize = True
        else:
            req.colorize = False

        # send to bot subsystem for processing
        self.process_message(req)

    def on_namreply(self, server, event):
        """NAMES requested, cache their opped status"""
        log.debug('[IRC] Updating NAMES list')
        args = event.arguments()
        channel = args[1]
        nicks = {}
        for nick in args[2].split():
            nick = nick.lower()
            opped = False
            if nick.startswith('@'):
                opped = True
                nick = nick[1:]
            elif nick.startswith('+'):
                nick = nick[1:]
            nicks[nick] = opped
        self.names[channel] = nicks
        self.last_names_update = unix_time()


class ProtocolHandler(IRCProtocol):
    pass

