"""Template for periodic event"""

from include.utils import Base

class PeriodicEvent(Base):

    def __init__(self, madcow):
        self.madcow = madcow
        self.enabled = True
        self.frequency = 60 # in seconds
        self.output = madcow.config.periodic.channel

    def process(self):
        """This is called by madcow, should return a string or None"""
