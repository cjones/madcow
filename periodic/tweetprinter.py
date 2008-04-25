#  tweetprinter.py
#  madcow
#  
#  Created by toast on 2008-04-21.
# 
# Periodically checks for fresh 'tweets' from friends and prints them to the channel
#

"""Prints tweets to the channel."""

from include.utils import Base
from include.utils import stripHTML
from include import twitter
import time

class PeriodicEvent(Base):

  def __init__(self, madcow):
    self.madcow = madcow
    self.enabled = madcow.config.twitter.enabled
    self.frequency = madcow.config.twitter.updatefreq
    self.output = madcow.config.twitter.channel
    self.__updatelast()
  
  def __updatelast(self):
    """Updates timestamp of last update."""
    self.lastupdate = time.gmtime()

  def __get_update_str(self):
    return time.strftime("%a, %d %b %Y %X GMT", self.lastupdate)

  def process(self):
    """This is called by madcow, should return a string or None"""
    try:
      tweets = twitter.Api().GetFriendsTimeline(user=self.madcow.config.twitter.username, since=self.__get_update_str())
    except Exception,e:
      print str(e)
      return None
    
    lines = []
    
    for t in reversed(tweets):
      if time.localtime(t.GetCreatedAtInSeconds()) < self.lastupdate: # twitter fails sometimes, so we do our own filter..
        print "ignoring old tweet with timestamp %s (TWITTER SUCKS)" % t.created_at
        continue
      
      line = ">> tweet from %s: %s <<" % (t.user.screen_name, stripHTML(t.text))
      lines.append(line)
    
    self.__updatelast()
    
    if lines:
      return "\n".join(lines)
    else:
      return None
