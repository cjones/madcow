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
import logging

class ProtocolHandler(madcow.Madcow, silc.SilcClient):
  def __init__(self, config=None, dir=None):
    madcow.Madcow.__init__(self, config=config, dir=dir)
    self.colorlib = ColorLib(type='mirc')

    keys = silc.create_key_pair("silc.pub", "silc.priv", passphrase="")
    nick = self.config.silcplugin.nick
    silc.SilcClient.__init__(self, keys, nick, nick, nick)

    self.allowThreading = True
    self.channels = re.split('\s*[,;]\s*', self.config.silcplugin.channels)

  def botName(self):
    return self.config.silcplugin.nick

  def connect(self):
    logging.info("connecting to %s:%s" % (self.config.silcplugin.host, self.config.silcplugin.port))
    self.connect_to_server(self.config.silcplugin.host, self.config.silcplugin.port)

  def start(self):
    self.connect()
    while True:
      self.run_one()
      time.sleep(0.2)

  def private_message(self, sender, flags, message):
    req = madcow.Request(message=message)
    req.nick = sender.nickname
    req.channel = None
    req.sendTo = sender
    req.private = True

    self.preProcess(req)
    req.addressed = True # privmsg implies addressing
    self.processMessage(req)

  def channel_message(self, sender, channel, flags, message):
    req = madcow.Request(message=message)
    req.nick = sender.nickname
    req.channel = channel.channel_name
    req.sendTo = channel
    req.private = False

    self.preProcess(req)
    self.processMessage(req)

  def preProcess(self, req):
    self.checkAddressing(req)

    if req.message.startswith('^'):
      req.message = req.message[1:]
      req.colorize = True
    else:
      req.colorize = False
  
  # not much of a point recovering from a kick when the silc code just segfaults on you :/
  #def notify_kicked(self, kicked, reason, kicker, channel):
  #  print 'SILC: Notify (Kick):', kicked, reason, kicker, channel

  def connected(self):
    logging.info("* Connected")
    for channel in self.channels:
      self.command_call("JOIN %s" % channel)

  def disconnected(self, msg):
    logging.warn("* Disconnected: %s" % msg)
    if self.config.silcplugin.reconnect:
      time.sleep(self.config.silcplugin.reconnectWait)
      self.connect()

  def output(self, req, message):
    if not message: return

    message = message.decode("ascii", "ignore") # remove unprintables

    if req.colorize:
      message = self.colorlib.rainbow(message)
    
    if req.private:
      self.send_to_user(req.sendTo, message)
    else:
      self.send_to_channel(req.sendTo, message)

  def send_to_channel(self, channel, message):
    for line in message.splitlines():
      self.send_channel_message(channel, line)

  def send_to_user(self, user, message):
    for line in message.splitlines():
      self.send_private_message(user, line)
