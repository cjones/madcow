#
#  silc.py
#  madcow-1.29
#
#  Created by Bryan Burns on 2007-06-19.
#
import madcow
import silc
import time
import re

class OutputHandler(madcow.madcow, silc.SilcClient):
  def __init__(self, config):
    self.config = config
    madcow.madcow.__init__(self)
    
    keys = silc.create_key_pair("silc.pub", "silc.priv", passphrase="")
    nick = self.config.silcplugin.nick
    silc.SilcClient.__init__(self, keys, nick, nick, nick)
    
    self.allowThreading = config.silcplugin.allowThreading
    self.channels = re.split('\s*[,;]\s*', self.config.silcplugin.channels)
  
  def botName(self):
    return self.config.silcplugin.nick
  
  def connect(self):
    print "connecting to", self.config.silcplugin.host, self.config.silcplugin.port
    self.connect_to_server(self.config.silcplugin.host, self.config.silcplugin.port)
  
  def start(self):
    self.connect()
    while True:
      self.run_one()
      time.sleep(0.2)
  
  def channel_message(self, sender, channel, flags, message):
    output = lambda m: self.send_to_channel(channel, m)
    response = self.processMessage(message, sender.nickname, channel.channel_name, False, output)
  
  def private_message(self, sender, flags, message):
    output = lambda m: self.send_to_user(sender, m)
    response = self.processMessage(message, sender.nickname, channel.channel_name, True, output)
  
  # not much of a point recovering from a kick when the silc code just segfaults on you :/
  #def notify_kicked(self, kicked, reason, kicker, channel):
  #  print 'SILC: Notify (Kick):', kicked, reason, kicker, channel
  
  def connected(self):
    print "* Connected"
    for channel in self.channels:
      self.command_call("JOIN %s" % channel)
  
  def disconnected(self, msg):
    print "* Disconnected: %s" % msg
    if self.config.silcplugin.reconnect:
      time.sleep(self.config.silcplugin.reconnectWait)
      self.connect()
  
  def send_to_channel(self, channel, message):
    self.send_channel_message(channel, message)
  
  def send_to_user(self, user, message):
    self.send_private_message(user, message)
    
