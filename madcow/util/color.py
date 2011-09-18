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

"""Color Library"""

import re

__version__ = u'0.6'
__author__ = u'cj_ <cjones@gruntle.org>'
__all__ = [u'ColorLib']

class UnknownProtocol(Exception):
    """Raised when protocol is not supported"""


class UnknownColor(Exception):
    """Raised when an unknown color is requested"""


class UnknownRainbowStyle(Exception):
    """Raised when an invalid style is requested"""


class ColorLib(object):
    _protocols = [u'mirc', u'ansi', u'html', None]
    _codes = {
        u'r': u'red',
        u'o': u'orange',
        u'y': u'yellow',
        u'Y': u'bright yellow',
        u'g': u'green',
        u'G': u'bright green',
        u'c': u'cyan',
        u'C': u'bright cyan',
        u'b': u'blue',
        u'B': u'bright blue',
        u'm': u'magenta',
        u'M': u'bright magenta',
        u'0': u'black',
        u'1': u'dark gray',
        u'2': u'light gray',
        u'w': u'white',
    }

    _color_map = {
        u'mirc': {
            u'red': u'5',
            u'orange': u'4',
            u'yellow': u'7',
            u'bright yellow': u'8',
            u'green': u'3',
            u'bright green': u'9',
            u'cyan': u'10',
            u'bright cyan': u'11',
            u'blue': u'2',
            u'bright blue': u'12',
            u'magenta': u'6',
            u'bright magenta': u'13',
            u'black': u'1',
            u'dark gray': u'14',
            u'light gray': u'15',
            u'white': u'0',
        },
        u'ansi': {
            u'red': u'1',
            u'orange': u'1b',
            u'yellow': u'3',
            u'bright yellow': u'3b',
            u'green': u'2',
            u'bright green': u'2b',
            u'cyan': u'6',
            u'bright cyan': u'6b',
            u'blue': u'4',
            u'bright blue': u'4b',
            u'magenta': u'5',
            u'bright magenta': u'5b',
            u'black': u'0',
            u'dark gray': u'0b',
            u'light gray': u'7',
            u'white': u'7b',
        },
        u'html': {
            u'red': u'#DF0009',
            u'orange': u'#FF000B',
            u'yellow': u'#C9D000',
            u'bright yellow': u'#FBFF00',
            u'green': u'#00D100',
            u'bright green': u'#00FF00',
            u'cyan': u'#00CECC',
            u'bright cyan': u'#00FFFE',
            u'blue': u'#1A00D1',
            u'bright blue': u'#2100FF',
            u'magenta': u'#E200D2',
            u'bright magenta': u'#FF00FF',
            u'black': u'#000000',
            u'dark gray': u'#808080',
            u'light gray': u'#CCCCCC',
            u'white': u'#FFFFFF',
        },
    }

    _rainbow_map = {
        u'rainbow': u'rryyggccbbmm',
        u'usa': u'ooowwwBBB',
        u'gray': u'111222',
        u'scale': u'ww22CC11CC22',
        u'xmas': u'rrgg',
        u'canada': u'ooowww',
    }

    # regex for stripping color codes
    _ansi_color = re.compile(r'\x1b\[[0-9;]+m')
    _mirc_color = re.compile(r"([\x02\x0F\x1F\x0E\x16\x1B]|\x03([0-9]{0,2})(,([0-9]{0,2}))?|\x04[0-9A-Fa-f]{6}(,([0-9A-Fa-f]){6})?)*")
    _html_color = re.compile(r'<span style=".*">')

    def __init__(self, protocol):
        if protocol not in self._protocols:
            raise UnknownProtocol(protocol)
        self.protocol = protocol
        self.rainbow_offset = {}

    def _normalize_color(self, color):
        color = color.lower().strip()
        if color in self._codes:
            color = self._codes[color]
        color = color.replace(u'bold', u'bright')
        color = color.replace(u'grey', u'gray')
        color = color.replace(u'purple', u'magenta')
        if color == u'gray':
            color = u'light gray'
        if color not in self._color_map[self.protocol]:
            raise UnknownColor, color
        return color

    def get_color(self, fg=None, bg=None, text=None):
        if not self.protocol:
            if text is None:
                return u''
            return text

        if not fg and not bg:
            return self.reset()
        if fg:
            fg = self._color_map[self.protocol][self._normalize_color(fg)]
        if bg:
            bg = self._color_map[self.protocol][self._normalize_color(bg)]
        if self.protocol == u'ansi':
            codes = []
            if fg is not None:
                if u'b' in fg:
                    codes.append(u'1')
                    fg = fg.replace(u'b', u'')
                codes.append(u'3' + fg)
            if bg is not None:
                bg = bg.replace(u'b', u'')
                codes.append(u'4' + bg)
            color = u'\x1b[%sm' % u';'.join(codes)
        elif self.protocol == u'mirc':
            codes = []
            if fg is None:
                codes.append(u'')
            else:
                codes.append(fg)
            if bg is not None:
                codes.append(bg)
            color = u'\x03' + u','.join(codes)
            if text is not None and text[0].isdigit():
                color += u'\x16\x16'
        elif self.protocol == u'html':
            codes = []
            if fg is not None:
                codes.append(u'color:' + fg)
            if bg is not None:
                codes.append(u'background-color:' + bg)
            color = u'<span style="%s">' % u';'.join(codes)
        if text is not None:
            return u'%s%s%s' % (color, text, self.reset())
        else:
            return color

    def reset(self):
        if self.protocol == u'ansi':
            return u'\x1b[0m'
        elif self.protocol == u'mirc':
            return u'\x0f'
        elif self.protocol == u'html':
            return u'</span>'
        else:
            return u''

    def rainbow(self, text, style=u'rainbow'):
        if not self.protocol:
            return text
        if style not in self._rainbow_map:
            raise UnknownRainbowStyle, style
        self.rainbow_offset.setdefault(style, 0)
        offset = self.rainbow_offset[style]
        output = u''
        colmap = self._rainbow_map[style]
        for line in text.splitlines():
            for i, ch in enumerate(line):
                if ch.isspace():
                    output += ch
                else:
                    color = colmap[(offset + i) % len(colmap)]
                    output += self.get_color(color, text=ch)
            offset += 1
            output += u'\n'
        self.rainbow_offset[style] = offset % 256
        return output

    def strip_color(self, text):
        if not self.protocol:
            return text
        if self.protocol == u'ansi':
            text = self._ansi_color.sub(u'', text)
        elif self.protocol == u'mirc':
            text = self._mirc_color.sub(u'', text)
        elif self.protocol == u'html':
            text = self._html_color.sub(u'', text)
        text = text.replace(self.reset(), u'')
        return text
