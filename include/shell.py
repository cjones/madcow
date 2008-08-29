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

import sys
import termios
import tty
import os
from select import select

__version__ = '0.1'
__author__ = 'cj_ <cjones@gruntle.org>'
__all__ = ['Shell']

class Shell(object):
    """Simple shell emulation.. might not work everywhere"""
    
    linefeed = '\r\n'
    backspace = '\x08\x7f'
    quit = '\x03\x04'
    ansi = '\x1b['
    up = ansi + 'A'
    down = ansi + 'B'
    right = ansi + 'C'
    left = ansi + 'D'

    def __init__(self, polls=[]):
        self.polls = list(polls)
        self.history = []

    def add_history(self, input):
        self.history.append(input)
        unique = []
        [unique.append(i) for i in reversed(self.history) if i not in unique]
        self.history = unique
        self.history.reverse()

    def readline(self, prompt='', fo=sys.stdout):
        line = ''
        buf = ''
        history = list(self.history)
        history.append(line)
        history.reverse()
        fo.write(prompt)
        fo.flush()
        pos = 0

        def redraw():
            new = prompt + line
            padding = 80 - len(new)
            fo.write('\r' + new)
            fo.write(' ' * padding)
            fo.write(self.left * padding)
            fo.flush()

        stdin = sys.stdin.fileno()
        old = termios.tcgetattr(stdin)
        try:
            tty.setraw(stdin)
            while True:
                for poll in self.polls:
                    poll()
                if stdin in select([stdin], [], [], 0.1)[0]:
                    ch = os.read(stdin, 1)
                else:
                    ch = ''
                if ch is not None and not len(ch):
                    continue
                if ch in self.quit:
                    line = 'quit'
                    redraw()
                    fo.write(self.linefeed)
                    fo.flush()
                    break
                if ch in self.linefeed:
                    fo.write(self.linefeed)
                    fo.flush()
                    break
                if ch in self.backspace:
                    if len(line):
                        line = line[:-1]
                        fo.write(self.left + ' ' + self.left)
                        fo.flush()
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
                elif buf.startswith(self.ansi):
                    buf = ''
                    post = 0
                    continue
                pos = 0
                fo.write(buf)
                fo.flush()
                line += buf
                buf = ''
            if len(line):
                self.add_history(line)
            return line
        finally:
            termios.tcsetattr(stdin, termios.TCSADRAIN, old)


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
