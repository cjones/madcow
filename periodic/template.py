"""Template for periodic event"""

from include.utils import Base

class PeriodicEvent(Base):

    def __init__(self, madcow):
        self.madcow = madcow
        self.enabled = True
        self.frequency = 60
        self.output = '#test'

    def process(self):
        pass

