#!/usr/bin/env python

"""Summon people"""

import sys
import re
from learn import Main as Learn
from include.utils import Base
import os
from smtplib import SMTP

class Main(Base):
    enabled = True
    pattern = re.compile(r'^\s*summons?\s+(\S+)(?:\s+(.*?))?\s*$')
    require_addressing = True


    help = 'summon <nick> [reason] - summon user'

    def __init__(self, madcow):
        self.learn = Learn(madcow)
        self.config = madcow.config

    def response(self, **kwargs):
        try:
            sendto, reason = kwargs['args']
            nick = kwargs['nick']
            email = self.learn.lookup('email', sendto)
            if email is None:
                raise Exception, "I don't know the email for %s" % sendto
            body = 'To: %s <%s>\n' % (sendto, email)
            body += 'From: %s\n' % (self.config.smtp.sender)
            body += 'Subject: Summon from %s' % nick
            body += '\n'
            body += 'You were summoned by %s. Reason: %s' % (nick, reason)

            smtp = SMTP(self.config.smtp.server)
            if len(self.config.smtp.user):
                smtp.login(self.config.smtp.user, self.config.smtp.password)
            smtp.sendmail(self.config.smtp.sender, [email], body)

            return "%s: summoned %s" % (nick, sendto)

        except Exception, e:
            return "%s: I couldn't make that summon: %s" % (nick, e)

