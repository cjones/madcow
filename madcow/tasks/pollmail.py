""" Imap Polling Task """

from madcow.util.imap import ImapPoller
from madcow.util import Task
from madcow.conf import settings

# the poller property is set by the pollmap module. Make sure it is enabled before enabling this.

class Main(Task):
    output = 'ALL'

    def init(self):
        # self.frequency = settings.POLLMAIL_FREQUENCY

        try:
            self.madcow.poller
        except AttributeError:
            self.madcow.poller = ImapPoller(self.madcow)

    def response(self, name, args, kwargs):
        self.log.debug("[PollMail Task] Polling IMAP")
        return self.madcow.poller()