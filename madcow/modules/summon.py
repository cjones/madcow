"""Summon people"""

import re
from learn import Main as Learn
from madcow.util import Module
from smtplib import SMTP

class Main(Module):

    pattern = re.compile(r'^\s*summons?\s+(\S+)(?:\s+(.*?))?\s*$')
    require_addressing = True
    help = u'summon <nick> [reason] - summon user'
    error = u"I couldn't make that summon"

    def init(self):
        self.learn = Learn(self.madcow)

    def response(self, nick, args, kwargs):
        sendto, reason = args
        email = self.learn.lookup(u'email', sendto)
        if email is None:
            return u"%s: I don't know the email for %s" % (nick, sendto)

        # just make all this shit ASCII, email is best that way...
        email = email.encode('ascii', 'replace')
        if reason:
            reason = reason.encode('ascii', 'replace')
        anick = nick.encode('ascii', 'replace')

        body = 'To: %s <%s>\n' % (sendto.encode('ascii', 'replace'), email)
        body += 'From: %s\n' % settings.SMTP_FROM
        body += 'Subject: Summon from %s' % anick
        body += '\n'
        body += 'You were summoned by %s. Reason: %s' % (anick, reason)

        smtp = SMTP(settings.SMTP_SERVER)
        if settings.SMTP_USER and settings.SMTP_PASS:
            smtp.login(settings.SMTP_USER, settings.SMTP_PASS)
        smtp.sendmail(settings.SMTP_FROM, [email], body)

        return u"%s: summoned %s" % (nick, sendto)
