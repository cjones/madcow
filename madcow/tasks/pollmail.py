from util.imap import Poller


""" Imap Polling Task """

# the poller property is set by the pollmap module. Make sure it is enabled before enabling this.

class Main(Task):
    frequency = settings.POLLMAIL_FREQUENCY

    def init(self, name, args, kwargs):
        if not self.madcow.poller:
           self.madcow.poller = Poller(self.madcow)

    def response(self):
        self.madcow.poller.poll()