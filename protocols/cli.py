from madcow import Madcow, Request
import os
from include.colorlib import ColorLib
import re
import logging as log
from include.shell import Shell

class ConsoleProtocol(Madcow):
    change_nick = re.compile(r'^\s*nick\s+(\S+)\s*$', re.I)

    def __init__(self, config=None, dir=None):
        self.colorlib = ColorLib(type='ansi')
        Madcow.__init__(self, config=config, dir=dir)
        self.user_nick = os.environ['USER']
        self.shell = Shell()

    def start(self, *args):
        while True:
            try:
                input = self.shell.readline('>>> ')
            except IOError:
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

    def _output(self, message, req):
        if req.colorize is True:
            message = self.colorlib.rainbow(message)

        print message


class ProtocolHandler(ConsoleProtocol):
    pass


