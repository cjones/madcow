#!/usr/bin/env python

"""
Summon people
"""

import sys
import re
import urllib
import learn
import os
from smtplib import SMTP

class MatchObject(object):

    def __init__(self, config=None, ns='madcow', dir=None):
        self.enabled = True
        self.pattern = re.compile(r'^\s*summons?\s+(\S+)(?:\s+(.*?))?\s*$')
        self.requireAddressing = True
        self.thread = False
        self.wrap = False
        self.ns = ns
        if dir is None:
            dir = os.path.abspath(os.path.dirname(sys.argv[0]) + '/..')
        self.dir = dir
        self.help = 'summon <nick> [reason] - summon user'
        self.learn = learn.MatchObject(ns=self.ns, dir=self.dir)
        self.config = config

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

if __name__ == '__main__':
    print MatchObject().response(nick=os.environ['USER'], args=sys.argv[1:])
    sys.exit(0)
