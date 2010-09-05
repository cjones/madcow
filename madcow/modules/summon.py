#!/usr/bin/env python
#
# Copyright (C) 2007, 2008 Christopher Jones
#
# This file is part of Madcow.
#
# Madcow is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Madcow is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Madcow.  If not, see <http://www.gnu.org/licenses/>.

"""Summon people"""

import re
from learn import Main as Learn
from madcow.util import Module
from smtplib import SMTP

class Main(Module):

    pattern = re.compile(r'^\s*summons?\s+(\S+)(?:\s+(.*?))?\s*$')
    require_addressing = True
    help = u'summon <nick> [reason] - summon user'

    def __init__(self, madcow):
        self.learn = Learn(madcow)

    def response(self, nick, args, kwargs):
        try:
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

        except Exception, error:
            log.warn(u'error in module %s' % self.__module__)
            log.exception(error)
            return u"%s: I couldn't make that summon: %s" % (nick, error)
