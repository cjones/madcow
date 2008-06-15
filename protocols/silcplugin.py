#
#  silc.py
#  madcow
#
#  Created by Bryan Burns on 2007-06-19.
#
import madcow
import silc
import time
import re
from include.colorlib import ColorLib
import logging as log

class SilcPlugin(madcow.Madcow, silc.SilcClient):

  def __init__(self, config, prefix):
    madcow.Madcow.__init__(self, config, prefix)
    self.colorlib = ColorLib('mirc')
    keys = silc.create_key_pair("silc.pub", "silc.priv", passphrase="")
    nick = self.config.silcplugin.nick
    silc.SilcClient.__init__(self, keys, nick, nick, nick)
    self.channels = self._delim.split(self.config.silcplugin.channels)

  def botname(self):
    return self.config.silcplugin.nick

  def connect(self):
    log.info("connecting to %s:%s" % (self.config.silcplugin.host, self.config.silcplugin.port))
    self.connect_to_server(self.config.silcplugin.host, self.config.silcplugin.port)

  def run(self):
    self.connect()
    while self.running:
      self.check_response_queue()
      try:
        self.run_one()
      except KeyboardInterrupt:
        self.running = False
      except Exception, e:
        log.error('exception caught in silc loop')
        log.exception(e)
      time.sleep(0.2)

  def private_message(self, sender, flags, message):
    self.on_message(sender, None, flags, message, True)

  def channel_message(self, sender, channel, flags, message):
    self.on_message(sender, channel, flags, message, False)

  def on_message(self, sender, channel, flags, message, private):
    req = madcow.Request(message=message)
    req.nick = sender.nickname
    req.private = private
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

  # not much of a point recovering from a kick when the silc code just segfaults on you :/
  #def notify_kicked(self, kicked, reason, kicker, channel):
  #  print 'SILC: Notify (Kick):', kicked, reason, kicker, channel

  def connected(self):
    log.info("* Connected")
    for channel in self.channels:
      self.command_call("JOIN %s" % channel)

  def disconnected(self, msg):
    log.warn("* Disconnected: %s" % msg)
    if self.config.silcplugin.reconnect:
      time.sleep(self.config.silcplugin.reconnectWait)
      self.connect()

  def protocol_output(self, message, req=None):
    if not message: return

    # XXX is this necessary now that main bot encodes to latin1/utf8?
    # BB: Yup, still needed :)
    # CJ: your mom.
    message = message.decode(self.config.main.charset, "ignore") # remove unprintables

    if req.colorize:
      message = self.colorlib.rainbow(message)
    
    if req.private:
      self.send_to_user(req.sendto, message)
    else:
      self.send_to_channel(req.sendto, message)

  # should these use irc's textwrap?
  # Nah, silc doesn't have message limits like IRC, so wrapping just
  # induces unnecessary ugliness

  def send_to_channel(self, channel, message):
    for line in message.splitlines():
      self.send_channel_message(channel, line)

  def send_to_user(self, user, message):
    for line in message.splitlines():
      self.send_private_message(user, line)


ProtocolHandler = SilcPlugin
