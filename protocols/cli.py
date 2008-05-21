from madcow import Madcow, Request
import os
from include.colorlib import ColorLib
import re
import logging as log
from include.shell import Shell

class ConsoleProtocol(Madcow):
    change_nick = re.compile(r'^\s*nick\s+(\S+)\s*$', re.I)
    _cli_usage = [
        'quit - quit madcow',
        'history - show history',
        'nick <nick> - change your nick',
    ]
    _prompt = '\x1b[1;31m>>>\x1b[0m '

    def __init__(self, config=None, dir=None):
        self.colorlib = ColorLib(type='ansi')
        Madcow.__init__(self, config=config, dir=dir)
        self.user_nick = os.environ['USER']
        self.shell = Shell()
        self.usageLines += self._cli_usage

    def start(self, *args):
        self.output("type 'help' for a list of commands")
        while True:
            try:
                input = self.shell.readline(self._prompt)
            except IOError:
                # this happens when you get EINTR from SIGHUP handling
                continue

            if input.lower() == 'quit':
                break

            if input.lower() == 'history':
                print 'history: %s' % repr(self.shell.history)

            if len(input) > 0:
                req = Request(message=input)
                req.nick = self.user_nick
                req.channel = 'cli'
                req.private = True
                req.addressed = True

                self.checkAddressing(req)

                if req.message.startswith('^'):
                    req.colorize = True
                    req.message = req.message[1:]

                self._processMessage(req)

    def _processMessage(self, req):
        try:
            self.user_nick = self.change_nick.search(req.message).group(1)
            self.output('nick changed to: %s' % self.user_nick, req)
            return
        except:
            pass
        self.processMessage(req)

    def _output(self, message, req=None):
        if req is None:
            req = Request(message=message)
        if req.colorize is True:
            message = self.colorlib.rainbow(message)

        print message


class ProtocolHandler(ConsoleProtocol):
    pass


