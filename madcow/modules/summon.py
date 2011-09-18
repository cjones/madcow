"""Summon people"""

import re
from learn import Main as Learn
from madcow.util import Module
from smtplib import SMTP
from madcow.conf import settings
from madcow.util.textenc import *

class Main(Module):

    pattern = re.compile(r'^\s*summons?\s+(\S+)(?:\s+(.*?))?\s*$')
    require_addressing = True
    help = u'summon <nick> [reason] - summon user'
    error = u"I couldn't make that summon"

    def init(self):
        self.learn = Learn(self.madcow)

    def response(self, nick, args, kwargs):
        sendto, reason = args
        email = self.learn.lookup('email', sendto)
        if email is None:
            return u"%s: I don't know the email for %s" % (nick, sendto)
        body = u'\n'.join((u'To: %s <%s>' % (sendto, email),
                           u'From: ' + settings.SMTP_FROM,
                           u'Subject: Summon from ' + nick,
                           u'',
                           u'You were summoned by %s. Reason: %s' % (nick, reason)))
        smtp = SMTP(settings.SMTP_SERVER)
        if settings.SMTP_USER and settings.SMTP_PASS:
            smtp.login(settings.SMTP_USER, settings.SMTP_PASS)
        smtp.sendmail(settings.SMTP_FROM, [encode(email, 'ascii')], encode(body))
        return u"%s: summoned %s" % (nick, sendto)
