import textwrap
import irclib
from madcow import Madcow, Request
import random
from time import sleep, time as unix_time
from madcow.conf import settings
from madcow.util.textenc import *

COLOR_SCHEME = 'mirc'

class IRCProtocol(Madcow):

    """Implements IRC protocol for madcow"""

    events = [u'welcome', u'disconnect', u'kick', u'privmsg', u'pubmsg', u'mode', 'nick',
              u'namreply', u'pong', u'action', u'nicknameinuse', u'topic', u'join']

    def __init__(self, base):
        super(IRCProtocol, self).__init__(base, scheme=COLOR_SCHEME)
        if settings.IRC_DEBUG:
            irclib.DEBUG = 1
        else:
            irclib.DEBUG = 0
        self.irc = irclib.IRC()
        self.server = self.irc.server()
        for event in self.events:
            self.log.info(u'[IRC] * Registering event: %s' % event)
            self.server.add_global_handler(event, getattr(self, u'on_' + event), 0)
        self.channels = settings.IRC_CHANNELS
        self.names = {}
        self.last_names_update = unix_time()

        # throttling
        self.delay = settings.IRC_DELAY_LINES / float(1000)
        self.last_response = 0.0

        # keepalive
        self.keepalive = settings.IRC_KEEPALIVE
        if self.keepalive:
            self.last_keepalive = self.last_pong = unix_time()
            self.keepalive_freq = settings.IRC_KEEPALIVE_FREQ
            self.keepalive_timeout = settings.IRC_KEEPALIVE_TIMEOUT

    def connect(self):
        self.log.info('[IRC] * Connecting to %s:%s', settings.IRC_HOST, settings.IRC_PORT)
        self.server.connect(settings.IRC_HOST, settings.IRC_PORT, settings.BOTNAME, ssl=settings.IRC_SSL,
                            password=settings.IRC_PASSWORD)
        if self.keepalive:
            self.last_keepalive = self.last_pong = unix_time()

    def stop(self):
        Madcow.stop(self)
        self.log.info('[IRC] * Quitting IRC')
        message = settings.IRC_QUIT_MESSAGE
        if message is None:
            message = u'no reason'
        self.server.disconnect(message)

    def on_nick(self, server, event):
        """Handler for nick change"""
        old = irclib.nm_to_n(event.source())
        new = event.target()
        for channel, nicks in self.names.iteritems():
            if old in nicks:
                self.logpublic(channel, '-+- %s is now known as %s' % (old, new))
                nicks[new] = nicks[old]
                del nicks[old]

    def on_join(self, server, event):
        """Handler for join channel"""
        nick, host = event.source().split('!', 1)
        channel = event.target()
        self.logpublic(channel, '-+- %s [%s] has joined %s' % (nick, host, channel))

    def on_mode(self, server, event):
        """Handler for mode changes"""
        nick = irclib.nm_to_n(event.source())
        channel = event.target()
        self.logpublic(channel, '-+- mode/%s [%s] by %s' % (channel, ' '.join(event.arguments()), nick))

    def on_topic(self, server, event):
        """Handler for topic changes"""
        nick = irclib.nm_to_n(event.source())
        channel = event.target()
        topic = event.arguments()[0]
        self.logpublic(channel, '-+- %s changed the topic of %s to: %s' % (nick, channel, topic))

    def on_nicknameinuse(self, server, event):
        old = self.botname()
        new = old + '_'
        self.log.warn('%s in use, trying %s', old, new)
        server.nick(new)

    def run(self):
        self.connect()
        while self.running:
            try:
                self.check_response_queue()
                self.irc.process_once(0.5)

                if self.keepalive:
                    now = unix_time()

                    # a new keepalive should be sent
                    if now - self.last_keepalive > self.keepalive_freq:
                        self.server.ping(now)
                        self.last_keepalive = now
                        self.log.debug('PING %s' % now)

                    # server seems unresponsive
                    if now - self.last_pong > self.keepalive_timeout:
                        self.log.warn('server appears to have gone away')
                        self.server.disconnect('server unresponsive')

            except KeyboardInterrupt:
                self.running = False
            except irclib.ServerNotConnectedError:
                # There's a bug where sometimes on_disconnect doesn't fire
                if settings.IRC_RECONNECT and self.running:
                    sleep(settings.IRC_RECONNECT_WAIT)
                    self.connect()
            except:
                self.log.exception('Error in IRC loop')

    def on_pong(self, server, event):
        # this should never happen, but don't take any chances
        if not self.keepalive:
            return

        pong = event.arguments()[0]
        try:
            pong = float(pong)
        except Exception, error:
            self.log.error('unexpected PONG reply: %s' % pong)
            self.log.exception(error)
            return
        now = unix_time()
        self.log.debug('PONG: latency = %s' % (now - pong))
        self.last_pong = now

    def on_action(self, server, event):
        self.on_message(server, event, False, True)

    def botname(self):
        return self.server.get_nickname()

    def on_welcome(self, server, event):
        """welcome event triggers startup sequence"""
        self.log.info(u'[IRC] * Connected')

        # identify with nickserv
        if settings.IRC_IDENTIFY_NICKSERV:
            self._privmsg(settings.IRC_NICKSERV_USER, 'IDENTIFY ' + settings.IRC_NICKSERV_PASS)

        # become an oper
        if settings.IRC_OPER:
            self.log.info(u'[IRC] * Becoming an OPER')
            self.server.oper(settings.IRC_OPER_USER, settings.IRC_OPER_PASS)

        # join all channels
        for channel in self.channels:
            self.log.info('[IRC] * Joining: %s', channel)
            self.server.join(channel)

    def on_disconnect(self, server, event):
        """disconnected from IRC"""
        self.log.warn(u'[IRC] * Disconnected from server')
        if settings.IRC_RECONNECT and self.running:
            sleep(settings.IRC_RECONNECT_WAIT)
            self.connect()

    def on_kick(self, server, event):
        """kicked from channel"""
        kicker = irclib.nm_to_n(event.source())
        channel = event.target()
        kicked, reason = event.arguments()

        self.logpublic(channel, '-+- %s was kicked from %s by %s [%s]' % (
            kicked, channel, kicker, reason if reason else ''))
        if kicked.lower() == server.get_nickname().lower():
            self.log.warn('I was kicked by %s (%s)', kicker, reason)
            if settings.IRC_REJOIN:
                sleep(settings.IRC_REJOIN_WAIT)
                server.join(channel)
                self._privmsg(channel, settings.IRC_REJOIN_MESSAGE)

    def protocol_output(self, message, req=None):
        """output to IRC"""
        if not message:
            return

        # color output if requested
        if req.colorize:
            style = random.choice(self.colorlib._rainbow_map.keys())
            message = self.colorlib.rainbow(message, style=style)

        # MUST wrap if unset because irc will boot you for exceeding maxlen
        wrap = settings.IRC_FORCE_WRAP
        if not wrap or wrap > 400:
            wrap = 400

        # each line gets its own privmsg
        output = []
        for line in message.splitlines():
            line = line.rstrip()
            if len(line) > wrap:
                for wrapped in textwrap.wrap(line, wrap):
                    output.append(wrapped)
            else:
                output.append(line)

        # send to IRC socket
        for line in (encode(line).replace('\x00', '') for line in output):
            if line:
                for channel in (self.channels if req.sendto == 'ALL' else [req.sendto]):
                    self._privmsg(channel, line)
                    self.logpublic(channel, '<%s> %s' % (self.botname(), line))

    def _privmsg(self, sendto, line):
        delta = unix_time() - self.last_response
        if delta < self.delay:
            sleep(self.delay - delta)
        self.server.privmsg(encode(sendto), line)
        self.last_response = unix_time()

    def on_privmsg(self, server, event):
        """private message received"""
        self.on_message(server, event, private=True)

    def on_pubmsg(self, server, event):
        """public message received"""
        self.on_message(server, event, private=False)

    def on_message(self, server, event, private, action=False):
        """process incoming messages"""
        req = Request(message=event.arguments()[0])
        req.nick = irclib.nm_to_n(event.source())
        req.channel = event.target()
        req.private = private
        req.action = action

        if private:
            req.sendto = req.nick
            req.addressed = True
        else:
            req.sendto = req.channel
            req.addressed = False

        req.message = decode(req.message)

        # strip control codes from incoming lines
        req.message = self.colorlib.strip_color(req.message)

        # strip adressing and set req attributes
        self.check_addressing(req)

        # lines that start with ^ will have their output rainbowed
        if req.message.startswith(u'^'):
            req.message = req.message[1:]
            req.colorize = True
        else:
            req.colorize = False

        # send to bot subsystem for processing
        self.process_message(req)

    def on_namreply(self, server, event):
        """NAMES requested, cache their opped status"""
        self.log.debug(u'[IRC] Updating NAMES list')
        args = event.arguments()
        channel = args[1]
        nicks = {}
        for nick in args[2].split():
            nick = nick.lower()
            opped = False
            if nick.startswith(u'@'):
                opped = True
                nick = nick[1:]
            elif nick.startswith(u'+'):
                nick = nick[1:]
            nicks[nick] = opped
        self.names[channel] = nicks
        self.last_names_update = unix_time()


class ProtocolHandler(IRCProtocol):

    allow_detach = True
