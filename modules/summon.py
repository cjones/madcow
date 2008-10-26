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
from include.utils import Module
from smtplib import SMTP
import logging as log

class Main(Module):

    pattern = re.compile(r'^\s*summons?\s+(\S+)(?:\s+(.*?))?\s*$')
    require_addressing = True
    help = 'summon <nick> [reason] - summon user'

    def __init__(self, madcow):
        self.learn = Learn(madcow)
        self.config = madcow.config

    def response(self, nick, args, kwargs):
        try:
            sendto, reason = args
            email = self.learn.lookup('email', sendto)
            if email is None:
                return "%s: I don't know the email for %s" % (nick, sendto)
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

        except Exception, error:
            log.warn('error in module %s' % self.__module__)
            log.exception(error)
            return "%s: I couldn't make that summon: %s" % (nick, error)
