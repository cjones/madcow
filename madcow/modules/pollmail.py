"""Poll email address"""

import re
import imaplib
from madcow.util import Module
from madcow.conf import settings
from madcow.util.text import *

class Main(Module):

    pattern = re.compile(r'^\s*mail\s+(.+?)\s*$')
    help = '\n'.join(['start - start automatic polling of email for messages', 'stop - stop automatic polling of email for messages', 'now - force one-time poll'])
    error = u"I had an error"

    def init(self):
        self.message = re.compile(r'{{(.+)}}')

    def response(self, nick, args, kwargs):
        if args[0].startswith('fo'):
            return u'%s: %s' % (nick, self.get_mail())
        return 'huh?'

    def get_mail(self):
        if settings.IMAP_USE_SSL:
            self.imap = imaplib.IMAP4_SSL(settings.IMAP_SERVER, settings.IMAP_PORT)
        else:
            self.imap = imaplib.IMAP4(settings.IMAP_SERVER, settings.IMAP_PORT)
        self.imap.login(settings.IMAP_USERNAME, settings.IMAP_PASSWORD)
        self.imap.select('Inbox')

        status, data = self.imap.search(None, 'ALL')
        msg = []
        for num in data[0].split():
            status, data = self.imap.fetch(num, '(RFC822)')
            msg.append(self.parse_mail(data[0][1]))
            self.imap.store(num, '+FLAGS', r'\Deleted') # mark deleted
        self.imap.expunge()

        # bye, imap server
        self.imap.close()
        self.imap.logout()
        return u'\n'.join(msg).strip()

    def parse_mail(self, mail):
        try:
            return u'\n'.join(self.message.search(mail).groups()).strip()
        except AttributeError:
            # No {{send this to irc}} markers
            pass
    
