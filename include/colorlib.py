#!/usr/bin/env python

"""Color Library"""

from utils import Base, Error
import re

__version__ = '0.5'
__author__ = 'cj_ <cjones@gruntle.org>'
__license__ = 'GPL'
__copyright__ = 'Copyright (C) 2008 Christopher Jones'
__all__ = ['ColorLib']

class UnknownProtocol(Error):
    """Raised when protocol is not supported"""


class UnknownColor(Error):
    """Raised when an unknown color is requested"""


class UnknownRainbowStyle(Error):
    """Raised when an invalid style is requested"""


class ColorLib(Base):
    _protocols = ['mirc', 'ansi', 'html']
    _codes = {
        'r': 'red',
        'o': 'orange',
        'y': 'yellow',
        'Y': 'bright yellow',
        'g': 'green',
        'G': 'bright green',
        'c': 'cyan',
        'C': 'bright cyan',
        'b': 'blue',
        'B': 'bright blue',
        'm': 'magenta',
        'M': 'bright magenta',
        '0': 'black',
        '1': 'dark gray',
        '2': 'light gray',
        'w': 'white',
    }

    _color_map = {
        'mirc': {
            'red': '5',
            'orange': '4',
            'yellow': '7',
            'bright yellow': '8',
            'green': '3',
            'bright green': '9',
            'cyan': '10',
            'bright cyan': '11',
            'blue': '2',
            'bright blue': '12',
            'magenta': '6',
            'bright magenta': '13',
            'black': '1',
            'dark gray': '14',
            'light gray': '15',
            'white': '0',
        },
        'ansi': {
            'red': '1',
            'orange': '1b',
            'yellow': '3',
            'bright yellow': '3b',
            'green': '2',
            'bright green': '2b',
            'cyan': '6',
            'bright cyan': '6b',
            'blue': '4',
            'bright blue': '4b',
            'magenta': '5',
            'bright magenta': '5b',
            'black': '0',
            'dark gray': '0b',
            'light gray': '7',
            'white': '7b',
        },
        'html': {
            'red': '#DF0009',
            'orange': '#FF000B',
            'yellow': '#C9D000',
            'bright yellow': '#FBFF00',
            'green': '#00D100',
            'bright green': '#00FF00',
            'cyan': '#00CECC',
            'bright cyan': '#00FFFE',
            'blue': '#1A00D1',
            'bright blue': '#2100FF',
            'magenta': '#E200D2',
            'bright magenta': '#FF00FF',
            'black': '#000000',
            'dark gray': '#808080',
            'light gray': '#CCCCCC',
            'white': '#FFFFFF',
        },
    }
    
    _rainbow_map = {
        'rainbow': 'rryyggccbbmm',
        'usa': 'ooowwwBBB',
        'gray': '111222',
        'scale': 'ww22CC11CC22',
        'xmas': 'rrgg',
        'canada': 'ooowww',
    }

    # regex for stripping color codes
    _ansi_color = re.compile(r'\x1b\[[0-9;]+m')
    _mirc_color = re.compile(r'\x03\d{0,2},?\d{1,2}(?:\x16{2})?')
    _html_color = re.compile(r'<span style=".*">')

    def __init__(self, protocol):
        if protocol not in self._protocols:
            raise UnknownProtocol, protocol
        self.protocol = protocol
        self.rainbow_offset = {}

    def _normalize_color(self, color):
        color = color.lower().strip()
        if color in self._codes:
            color = self._codes[color]
        color = color.replace('bold', 'bright')
        color = color.replace('grey', 'gray')
        color = color.replace('purple', 'magenta')
        if color == 'gray':
            color = 'light gray'
        if color not in self._color_map[self.protocol]:
            raise UnknownColor, color
        return color

    def get_color(self, fg=None, bg=None, text=None):
        if not fg and not bg:
            return self.get_reset()
        if fg:
            fg = self._color_map[self.protocol][self._normalize_color(fg)]
        if bg:
            bg = self._color_map[self.protocol][self._normalize_color(bg)]
        if self.protocol == 'ansi':
            codes = []
            if fg is not None:
                if 'b' in fg:
                    codes.append('1')
                    fg = fg.replace('b', '')
                codes.append('3' + fg)
            if bg is not None:
                bg = bg.replace('b', '')
                codes.append('4' + bg)
            color = '\x1b[%sm' % ';'.join(codes)
        elif self.protocol == 'mirc':
            codes = []
            if fg is None:
                codes.append('')
            else:
                codes.append(fg)
            if bg is not None:
                codes.append(bg)
            color = '\x03' + ','.join(codes)
            if text is not None and text[0].isdigit():
                color += '\x16\x16'
        elif self.protocol == 'html':
            codes = []
            if fg is not None:
                codes.append('color:' + fg)
            if bg is not None:
                codes.append('background-color:' + bg)
            color = '<span style="%s">' % ';'.join(codes)
        if text is not None:
            return '%s%s%s' % (color, text, self.reset())
        else:
            return color

    def reset(self):
        if self.protocol == 'ansi':
            return '\x1b[0m'
        elif self.protocol == 'mirc':
            return '\x0f'
        elif self.protocol == 'html':
            return '</span>'

    def rainbow(self, text, style='rainbow'):
        if not self._rainbow_map.has_key(style):
            raise UnknownRainbowStyle, style
        self.rainbow_offset.setdefault(style, 0)
        offset = self.rainbow_offset[style]
        output = ''
        colmap = self._rainbow_map[style]
        for line in text.splitlines():
            for i, ch in enumerate(line):
                if ch.isspace():
                    output += ch
                else:
                    color = colmap[(offset + i) % len(colmap)]
                    output += self.get_color(color, text=ch)
            offset += 1
            output += '\n'
        self.rainbow_offset[style] = offset % 256
        return output

    def strip_color(self, text):
        if self.protocol == 'ansi':
            text = self._ansi_color.sub('', text)
        elif self.protocol == 'mirc':
            text = self._mirc_color.sub('', text)
        elif self.protocol == 'html':
            text = self._html_color.sub('', text)
        text = text.replace(self.reset(), '')
        return text

