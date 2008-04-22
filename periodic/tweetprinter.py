#  tweetprinter.py
#  madcow
#  
#  Created by toast on 2008-04-21.
# 
# Periodically checks for fresh 'tweets' from friends and prints them to the channel
#

"""Prints tweets to the channel."""

from include.utils import Base
from include import twitter
import time

class PeriodicEvent(Base):

  def __init__(self, madcow):
    self.madcow = madcow
    self.enabled = True
    self.frequency = madcow.config.twitter.updatefreq
    self.output = madcow.config.periodic.channel
    self.__updatelast()
  
  def __updatelast(self):
    """Updates timestamp of last update."""
    self.lastupdate = time.strftime("%a, %d %b %Y %X GMT", time.gmtime())

  def process(self):
    """This is called by madcow, should return a string or None"""
    print "checking for new tweets... last update is %s" % self.lastupdate
    try:
      tweets = twitter.Api().GetFriendsTimeline(user=self.madcow.config.twitter.username, since=self.lastupdate)
    except Exception,e:
      print str(e)
      self.__updatelast()
      return None
    self.__updatelast()
    
    lines = []
    
    for t in tweets:
      line = "tweet from %s: %s" % (t.user.screen_name, t.text)
      lines.append(line)
    
    if lines:
      return "\n".join(lines)
    else:
      return None
