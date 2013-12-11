""" Does IMAP parsing, and sends messages to the proper output """

from madcow.conf import settings
import re
import imaplib
import itertools
import json as jsonlib

class ImapPoller(object):
    frequency = settings.POLLMAIL_FREQUENCY
    started = settings.POLLMAIL_AUTOSTART

    def __init__(self, madcow):
        self.madcow = madcow

        if None in [settings.IMAP_SERVER, settings.IMAP_PORT, settings.IMAP_PASSWORD, settings.IMAP_USERNAME]:
            raise ValueError("Imap Settings has a None value.")

    def __call__(self, forced=False):
        msgs = []

        if not self.started and not forced:
            return

        self.madcow.log.debug("Getting mail!")
        mails = self.poll()
        self.madcow.log.debug("Total mail %i" % len(mails))

        for mail in mails:
            self.madcow.log.debug("Checking next mail.")
            jsons = self.parse_mail(mail)
            self.madcow.log.debug("JSONs found: %i" % len(jsons))

            if (not self.security(jsons)):
                self.madcow.log.debug("Security check failed.")
                continue  # Password in email not found.

            self.madcow.log.debug("Security check succeeded.")
            msgs += [json['msg'] for json in jsons if 'msg' in json]

        return '\n'.join(msgs)

    def start(self, nick):
        if nick != settings.OWNER_NICK:
            return 'Permission denied.'
        self.started = True
        return 'Okay'

    def stop(self, nick):
        if nick != settings.OWNER_NICK:
            return 'Permission denied.'
        self.started = False
        return 'Okay'

    def poll(self):
        # Open the IMAP Session
        if settings.IMAP_USE_SSL:
            imap = imaplib.IMAP4_SSL(settings.IMAP_SERVER, settings.IMAP_PORT)
        else:
            imap = imaplib.IMAP4(settings.IMAP_SERVER, settings.IMAP_PORT)
        imap.login(settings.IMAP_USERNAME, settings.IMAP_PASSWORD)
        imap.select('Inbox')

        # Get all mail
        status, data = imap.search(None, 'ALL')
        mail_ixs = data[0].split()
        mails = [self.fetch(imap, ix) for ix in mail_ixs]

        # Delete all mail
        imap.expunge()

        # Close IMAP Session
        imap.close()
        imap.logout()

        return mails

    def fetch(self, imap, ix):
        status, data = imap.fetch(ix, '(RFC822)')
        imap.store(ix, '+FLAGS', r'\Deleted')

        # data is a list of length 1 with a tuple of length 2 with
        # the structure ("%ix (RFC822)", "%mail")
        # We just want the mail portion.
        return data[0][1]


    # This is a mess.
    def parse_mail(self, mail):
        jsons = []

        self.madcow.log.debug("Parsing Mail")

        for match in settings.POLLMAIL_JSON_REGEX.findall(mail):
            self.madcow.log.debug("Possible JSON found: %s" % match)

            try:
                json = jsonlib.loads(match)  # Throws ValueError if not JSON
                self.madcow.log.debug("Is JSON")
                jsons.append(json)
            except ValueError:
                self.madcow.log.debug("Not JSON")

        return jsons

    def security(self, jsons):
        if not settings.POLLMAIL_USE_PASSWORD:
            return True

        for json in jsons:
            if ('password' in json) and (json['password'] == settings.POLLMAIL_PASSWORD):
                return True

        return False