from madcow import Madcow, Request
import os
from include.colorlib import ColorLib
import re
import sys
import termios
import tty

class ConsoleProtocol(Madcow):
    change_nick = re.compile(r'^\s*nick\s+(\S+)\s*$', re.I)

    def __init__(self, config=None, dir=None):
        self.colorlib = ColorLib(type='ansi')
        Madcow.__init__(self, config=config, dir=dir)
        self.user_nick = os.environ['USER']
        self.shell = Shell()
        self.history = []

    def start(self, *args):
        while True:
            input = self.shell.readline('>>> ', history=self.history)
            self.history.append(input)

            if input.lower() == 'quit':
                break

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


class Shell:
    """Simple shell emulation.. might not work everywhere"""
    
    linefeed = '\r\n'
    backspace = '\x08\x7f'
    ansi = '\x1b['
    up = ansi + 'A'
    down = ansi + 'B'
    right = ansi + 'C'
    left = ansi + 'D'

    def getch(self):
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        return ch

    def rotate(self, seq, n=1):
        n = n % len(seq)
        return seq[n:] + seq[:n]

    def readline(self, prompt='', history=[], fo=sys.stdout):
        fo.write(prompt)
        line = ''
        history.reverse()
        buf = ''

        def redraw():
            new = prompt + line
            padding = 80 - len(new)
            fo.write('\r' + new)
            fo.write(' ' * padding)
            fo.write(self.left * padding)

        while True:
            ch = self.getch()
            if ch == '\x03':
                raise KeyboardInterrupt
            if ch == '\x04':
                raise EOFError
            if ch in self.linefeed:
                fo.write(self.linefeed)
                break
            if ch in self.backspace:
                if len(line):
                    line = line[:-1]
                    fo.write(self.left + ' ' + self.left)
                continue
            buf += ch
            if buf == self.up:
                buf = ''
                if history:
                    line = history[0]
                    history = self.rotate(history)
                    redraw()
                continue
            elif buf == self.down:
                buf = ''
                if history:
                    line = history[0]
                    history = self.rotate(history, -1)
                    redraw()
                continue
            elif buf == self.ansi[:len(buf)]:
                continue
            fo.write(buf)
            line += buf
            buf = ''
        return line

