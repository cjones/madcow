import urllib2
from madcow import __version__ as current_version
from madcow.conf import settings
from madcow.util import Task

class Main(Task):

    url = 'http://dis.gruntle.org/app/madcow/latest/'
    agent = 'Madcow Updater v' + current_version
    msg_fmt = 'Madcow v%(new_version)s is available, you have v%(current_version)s.  Visit http://madcow.googlecode.com/ to update.\x07'

    def init(self):
        self.frequency = settings.UPDATER_FREQ
        self.output = settings.UPDATER_ANNOUNCE_CHANNELS
        self.opener = urllib2.build_opener()
        self.opener.addheaders = [('User-Agent', self.agent)]

    def response(self, *args):
        """This is called by madcow, should return a string or None"""
        self.log.info('checking for updates for madcow...')
        new_version = self.opener.open(self.url).read().strip()
        if numeric(new_version) > numeric(current_version):
            msg = self.msg_fmt % {'current_version': current_version, 'new_version': new_version}
            self.log.warn(msg)
            return msg
        else:
            self.log.info('you are up to date')


def numeric(version):
    """Convert multi-part version string into a numeric value"""
    return sum(int(part) * (100 ** (2 - i)) for i, part in enumerate(version.split('.')) if part.strip().isdigit())
