""" Imap Polling Task """

from madcow.util.imap import ImapPoller

# the poller property is set by the pollmap module. Make sure it is enabled before enabling this.

class Main(Task):
    frequency = settings.POLLMAIL_FREQUENCY

    def init(self, name, args, kwargs):
        if not self.madcow.poller:
           self.madcow.poller = ImapPoller(self.madcow)

    def response(self):
        self.madcow.poller.poll()