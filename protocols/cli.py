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

import sys
from madcow import Madcow, Request
import os
import re
from include.shell import Shell

COLOR_SCHEME = 'ansi'

class ConsoleProtocol(Madcow):

    _new_nick = re.compile(r'^\s*nick\s+(\S+)\s*$', re.I)
    _prompt = '\x1b[1;31m>>>\x1b[0m '
    _clear = u'\x1b[H\x1b[J'
    _cli_usage = [u'quit - quit madcow',
                  u'history - show history',
                  u'nick <nick> - change your nick',
                  u'clear - clear screen']

    def __init__(self, config, prefix, scheme=None):
        if scheme is None:
            scheme = COLOR_SCHEME
        super(ConsoleProtocol, self).__init__(config, prefix, scheme)
        self.user_nick = os.environ[u'USER']
        self.shell = Shell(polls=[self.check_response_queue])
        self.usage_lines += self._cli_usage

    def run(self):
        self.output(u"type 'help' for a list of commands")
        while self.running:
            self.check_response_queue()
            try:
                input = self.shell.readline(self._prompt)
            except IOError:
                # this happens when you get EINTR from SIGHUP handling
                continue

            input = input.decode(sys.stdin.encoding, 'replace')

            if input.lower() == u'quit':
                break

            if input.lower() == u'history':
                print u'history: %s' % repr(self.shell.history)
                continue

            if input.lower() == u'clear':
                sys.stdout.write(self._clear)
                continue

            if len(input) > 0:
                req = Request(message=input)
                req.nick = self.user_nick
                req.channel = u'cli'
                req.private = True
                req.addressed = True

                self.check_addressing(req)

                if req.message.startswith(u'^'):
                    req.colorize = True
                    req.message = req.message[1:]

                try:
                    self.user_nick = self._new_nick.search(req.message).group(1)
                    self.output(u'nick changed to: %s' % self.user_nick, req)
                    continue
                except:
                    pass
                self.process_message(req)

    def protocol_output(self, message, req=None):
        if req is not None and req.colorize is True:
            message = self.colorlib.rainbow(message)
        print message.encode(self.charset, 'replace')


class ProtocolHandler(ConsoleProtocol):
    pass


