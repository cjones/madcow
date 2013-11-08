from madcow.conf import settings
import re
import imaplib

class ImapPoller(object):
    started = settings.POLLMAIL_AUTOSTART
    message = re.compile(r'{{(.+)}}')

    def __init__(self, madcow):
        self.madcow = madcow

        try:
            self.madcow.irc  # throws AttributeError if not IRC Connection
            self.irc = True
        except AttributeError:
            self.irc = False

    def __call__(self, forced=False):
        if not started and not forced:
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
            return 'Permission denied.'
        started = True
        return 'Okay'

    def stop(self, nick):
        if nick != settings.OWNER_NICK:
            return 'Permission denied.'
        started = False
        return 'Okay'

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
            if ('password' in json) and (json['password'] == settings.POLLMAIL_PASSWORD):
                return True

        return False

    def send_msg(self, json):
        if 'channels' in json and self.irc:
                channels = json['channels']
                irc = self.madcow.irc

                irc.privmsg_many(channels, json['msg'])
        else:
            self.madcow.output(json['msg'])