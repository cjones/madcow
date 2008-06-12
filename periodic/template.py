"""Template for periodic event"""

from include.utils import Base

class Main(Base):

    def __init__(self, madcow):
        self.madcow = madcow

        """
        Add a section in madcow.ini with appropriate defaults, like so:

        [modulename]
        enabled=no
        updatefreq=60
        channel=#madcow

        replacing "modulename" with a one-word descriptor of this module
        in both the ini header and the code below
        """

        self.enabled = madcow.config.modulename.enabled
        self.frequency = madcow.config.modulename.updatefreq
        self.output = madcow.config.modulename.channel

    def response(self, *args):
        """This is called by madcow, should return a string or None"""

