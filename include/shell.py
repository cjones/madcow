#!/usr/bin/env python

import sys
import termios
import tty

__version__ = '0.1'
__author__ = 'cj_ <cjones@gruntle.org>'
__license__ = 'GPL'
__copyright__ = 'Copyright (C) 2008 Christopher Jones'
__all__ = ['Shell']

class Shell:
    """Simple shell emulation.. might not work everywhere"""
    
    linefeed = '\r\n'
    backspace = '\x08\x7f'
    quit = '\x03\x04'
    ansi = '\x1b['
    up = ansi + 'A'
    down = ansi + 'B'
    right = ansi + 'C'
    left = ansi + 'D'

    def __init__(self):
        self.history = []

    def add_history(self, input):
        self.history.append(input)
        unique = []
        [unique.append(i) for i in reversed(self.history) if i not in unique]
        self.history = unique
        self.history.reverse()

    def getch(self):
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        return ch

    def readline(self, prompt='', fo=sys.stdout):
        line = ''
        buf = ''
        history = list(self.history)
        history.append(line)
        history.reverse()
        fo.write(prompt)
        pos = 0

        def redraw():
            new = prompt + line
            padding = 80 - len(new)
            fo.write('\r' + new)
            fo.write(' ' * padding)
            fo.write(self.left * padding)

        while True:
            ch = self.getch()
            if ch in self.quit:
                line = 'quit'
                redraw()
                fo.write(self.linefeed)
                break
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
                if self.history:
                    if pos == 0:
                        history[0] = line
                    pos += 1
                    if pos == len(history):
                        pos -= 1
                    line = history[pos]
                    redraw()
                continue
            elif buf == self.down:
                buf = ''
                if history:
                    pos -= 1
                    if pos < 0:
                        pos = 0
                    line = history[pos]
                    redraw()
                continue
            elif buf == self.ansi[:len(buf)]:
                continue
            pos = 0
            fo.write(buf)
            line += buf
            buf = ''
        if len(line):
            self.add_history(line)
        return line


def main():
    sh = Shell()
    prompt = '>>> '
    while True:
        input = sh.readline(prompt)
        if input == 'quit':
            break
        print 'got: %s' % repr(input)

if __name__ == '__main__':
    sys.exit(main())
