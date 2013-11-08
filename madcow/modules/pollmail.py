"""Poll email address"""

import re
import imaplib
import json as JSON
from madcow.util import Module
from madcow.conf import settings
from madcow.util.text import *

# Todo:
# Figure out how to get "channels" working
# Find a way to crate a single Poller that it used by the PollTask and the MainModule
# Figure out how to set frequency. Assume for now that its seconds.



class ImapPoller(object):
    started = settings.POLLMAIL_AUTOSTART

    def response(self):
        if not started:
            return

        mails = self.poll()

        for mail in mails:
            jsons = self.parse_mail(mail)

            if (not self.security(jsons)):
                return  # Password in email not found.

        for json in jsons:
            if 'msg' in json:
                self.send_msgs(json)

    def start(self, nick):
        if nick != settings.OWNER_NICK:
            return
        started = True

    def stop(self, nick):
        if nick != settings.OWNER_NICK:
            return
        started = False

    def poll(self):
        if settings.IMAP_USE_SSL:
            imap = imaplib.IMAP4_SSL(settings.IMAP_SERVER, settings.IMAP_PORT)
        else:
            imap = imaplib.IMAP4(settings.IMAP_SERVER, settings.IMAP_PORT)
        imap.login(settings.IMAP_USERNAME, settings.IMAP_PASSWORD)
        imap.select('Inbox')

        status, data = imap.search(None, 'ALL')
        mails = data[0].split()
        response = []
        for ix in data[0].split():
            status, data = imap.fetch(ix, '(RFC822)')
            response.append(self.parse_mail(data[0][1]))
            imap.store(ix, '+FLAGS', r'\Deleted') # mark deleted
        imap.expunge()

        # bye, imap server
        imap.close()
        imap.logout()
        return u'\n'.join(response).strip()


    # This is a mess.
    def parse_mail(self, mail):
        jsons = []

        for match in self.message.findall(mail):
            try:
                json = JSON.loads(match)  # Throws ValueError if not JSON
                jsons.append(json)
            except ValueError:
                pass

        return jsons

    def security(self, jsons):
        if not settings.POLLMAIL_USE_PASSWORD:
            return True

        for json in jsons:
            if 'password' in json && json['password'] is settings.POLLMAIL_PASSWORD:
                return True

        return False

    def send_msg(self, json):
        if 'channels' in json:
            channels = json['channels']
        else:
            channels = None ### get_current_channels

        for channel in channels:
            pass
            ## Send json['msg']

class Main(Module):
    poller = Poller() # FIXME
    pattern = re.compile(r'^\s*mail\s+(.+?)\s*$')
    help = '\n'.join(['start - start automatic polling of email for messages', 'stop - stop automatic polling of email for messages', 'now - force one-time poll'])
    error = u"I had an error"

    def init(self):
        self.message = re.compile(r'{{(.+)}}')

    def response(self, nick, args, kwargs):
        if args[0] is "pollmail":
            command = args[1]

            if command is 'now':
                self.poller.poll()
                return

            if command is 'start':
                return self.poller.start(nick)

            if command is 'stop':
                return self.poller.stop(nick)

class ImapTask(Task):
    poller = Poller() # FIXME
    frequency = settings.POLLMAIL_FREQUENCY

    def response(self):
        self.poller.poll()