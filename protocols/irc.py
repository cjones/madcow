import textwrap
from include import irclib
import time
import re
import sys
from madcow import Madcow, Request
from include.colorlib import ColorLib
import random
import logging as log
from time import time as unix_time

class IRCProtocol(Madcow):

    def __init__(self, config=None, dir=None):
        self.colorlib = ColorLib(type='mirc')
        Madcow.__init__(self, config=config, dir=dir)
        if log.root.level <= log.DEBUG:
            irclib.DEBUG = 1
        else:
            irclib.DEBUG = 0
        self.irc = irclib.IRC()
        self.server = self.irc.server()
        self.events = ['welcome', 'disconnect', 'kick', 'privmsg', 'pubmsg',
                'namreply']
        if self.config.irc.channels is not None:
            self.channels = self.reDelim.split(self.config.irc.channels)
        else:
            self.channels = []
        self.names = {}
        self.last_names_update = unix_time()

    def connect(self):
        log.info('[IRC] * Connecting to %s:%s' % (self.config.irc.host,
            self.config.irc.port))
        self.server.connect(self.config.irc.host, self.config.irc.port,
                self.config.irc.nick)

    def start(self):
        self.connect()
        for event in self.events:
            log.info('[IRC] * Registering event: %s' % event)
            self.server.add_global_handler(event,
                    getattr(self, 'on_' + event), 0)

        while True:
            try:
                self.irc.process_once(0.2)
            except Exception, e:
                log.warn('EINTR detected in irc loop')
                log.exception(e)

    def botName(self):
        return self.server.get_nickname()

    # welcome event triggers startup sequence
    def on_welcome(self, server, event):
        log.info('[IRC] * Connected')

        # identify with nickserv
        if self.config.irc.nickServUser and self.config.irc.nickServPass:
            self.server.privmsg(self.config.irc.nickServUser,
                    'IDENTIFY %s' % self.config.irc.nickServPass)

        # become an oper
        if self.config.irc.oper is True:
            log.info('[IRC] * Becoming an OPER')
            self.server.oper(self.config.irc.operUser, self.config.irc.operPass)

        # join all channels
        for channel in self.channels:
            log.info('[IRC] * Joining: %s' % channel)
            self.server.join(channel)

    # when losing connection, reconnect if configured to do so, otherwise exit
    def on_disconnect(self, server, event):
        log.warn('[IRC] * Disconnected from server')

        if self.config.irc.reconnect is True:
            if self.config.irc.reconnectWait > 0:
                time.sleep(self.config.irc.reconnectWait)
            self.connect()
        else:
            sys.exit(1)

    # when kicked, rejoin channel if configured to do so
    def on_kick(self, server, event):
        log.warn('[IRC] * Kicked from %s by %s' % (event.arguments()[0],
            event.target()))
        if event.arguments()[0].lower() == server.get_nickname().lower():
            if self.config.irc.rejoin is True:
                if self.config.irc.rejoinWait > 0:
                    time.sleep(self.config.irc.rejoinWait)
                server.join(event.target())
                server.privmsg(event.target(), self.config.irc.rejoinReply)

    # function to putput to IRC
    def _output(self, message, req):
        if message is None:
            return

        # IRC really doesn't like null characters
        message = message.replace('\x00', '')
        if len(message) == 0:
            return

        if req.colorize is True:
            style = random.choice(ColorLib.rainbowStyles)
            message = self.colorlib.rainbow(message, style=style)

        try:
            wrap = self.config.irc.wrapsize
        except:
            wrap = 400

        output = []
        for line in message.splitlines():
            for wrapped in textwrap.wrap(line, wrap):
                output.append(wrapped)

        for line in output:
            self.server.privmsg(req.sendTo, line)

    def on_privmsg(self, server, event):
        log.info('[IRC] PRIVMSG from %s: %s' % (event.source(),
            event.arguments()[0]))
        self.on_message(server, event, private=True)

    def on_pubmsg(self, server, event):
        log.info('[IRC] <%s/%s> %s' % (event.source(), event.target(),
            event.arguments()[0]))
        self.on_message(server, event, private=False)

    def on_message(self, server, event, private):
        req = Request(message=event.arguments()[0])
        req.nick = irclib.nm_to_n(event.source())
        req.channel = event.target()
        req.private = private

        if private is True:
            req.sendTo = req.nick
            req.addressed = True
        else:
            req.sendTo = req.channel

        self.preProcess(req)
        self.processMessage(req)

    def preProcess(self, req):
        self.checkAddressing(req)

        if req.message.startswith('^'):
            req.message = req.message[1:]
            req.colorize = True
        else:
            req.colorize = False

    def on_namreply(self, server, event):
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


