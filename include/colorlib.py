"""
Library for colorizing objects in ANSI, mIRC or HTML.
"""

__version__ = '0.3'
__author__ = 'Christopher Jones <cjones@gruntle.org>'
__copyright__ = """
Copyright (C) 2007 Christopher Jones <cjones@gruntle.org>

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA
"""


class ColorLibError(Exception):
    """
    Base class for ColorLib exceptions
    """
    def __init__(self, error=None):
        self.error = error

    def __str__(self):
        return self.error


class ColorTypeUnknown(ColorLibError):
    """
    Raised when the requested color handler is unknown
    """

class UnknownColor(ColorLibError):
    """
    Raised when user tries to use an unknown color
    """


class UnknownRainbowStyle(ColorLibError):
    """
    Raised when an unknown style is chosen for rainbow()
    """


class ColorLib(object):
    """
    Base class for color handling
    """

    colorMap = {
        'red':            { 'code': 'r', 'mirc': '5',  'ansi': '1',  'html': '#DF0009' },
        'orange':         { 'code': 'o', 'mirc': '4',  'ansi': '1b', 'html': '#FF000B' },
        'yellow':         { 'code': 'y', 'mirc': '7',  'ansi': '3',  'html': '#C9D000' },
        'bright yellow':  { 'code': 'Y', 'mirc': '8',  'ansi': '3b', 'html': '#FBFF00' },
        'green':          { 'code': 'g', 'mirc': '3',  'ansi': '2',  'html': '#00D100' },
        'bright green':   { 'code': 'G', 'mirc': '9',  'ansi': '2b', 'html': '#00FF00' },
        'cyan':           { 'code': 'c', 'mirc': '10', 'ansi': '6',  'html': '#00CECC' },
        'bright cyan':    { 'code': 'C', 'mirc': '11', 'ansi': '6b', 'html': '#00FFFE' },
        'blue':           { 'code': 'b', 'mirc': '2',  'ansi': '4',  'html': '#1A00D1' },
        'bright blue':    { 'code': 'B', 'mirc': '12', 'ansi': '4b', 'html': '#2100FF' },
        'magenta':        { 'code': 'm', 'mirc': '6',  'ansi': '5',  'html': '#E200D2' },
        'bright magenta': { 'code': 'M', 'mirc': '13', 'ansi': '5b', 'html': '#FF00FF' },

        'black':          { 'code': '0', 'mirc': '1',  'ansi': '0',  'html': '#000000' },
        'dark gray':      { 'code': '1', 'mirc': '14', 'ansi': '0b', 'html': '#808080' },
        'light gray':     { 'code': '2', 'mirc': '15', 'ansi': '7',  'html': '#CCCCCC' },
        'white':          { 'code': 'w', 'mirc': '0',  'ansi': '7b', 'html': '#FFFFFF' },
    }

    types = ('mirc', 'ansi', 'html')
    colors = colorMap.keys()
    codes = dict([(d['code'], color) for color, d in colorMap.items()])

    rainbowmap = {
        'rainbow': 'rryyggccbbmm',
        'usa':     'ooowwwBBB',
        'gray':    '111222',
        'scale':   'ww22CC11CC22',
        'xmas':    'rrgg',
        'canada':  'ooowww',
    }

    rainbowStyles = rainbowmap.keys()

    def __init__(self, type=None):
        if type not in self.types:
            raise ColorTypeUnknown, 'type must be one of: %s' % ', '.join(self.types)

        self.rainbowOffset = {}
        self.type = type

    def _normalizeColorName(self, color=None):
        if color is None: return
        color = color.lower()
        color = ' '.join(color.split())
        color = color.replace('bold', 'bright')
        color = color.replace('grey', 'gray')
        color = color.replace('purple', 'magenta')
        if color == 'gray':
            color = 'light gray'
        if len(color) == 1 and self.codes.has_key(color):
            color = self.codes[color]
        if self.colorMap.has_key(color) is False:
            raise UnknownColor, 'known colors: %s' % ', '.self.colors
        return color

    def getColor(self, fg=None, bg=None, type=None, char=None):
        if type is None: type = self.type
        if fg is None and bg is None: return self.reset()
        if fg is not None: fg = self.colorMap[self._normalizeColorName(fg)][type]
        if bg is not None: bg = self.colorMap[self._normalizeColorName(bg)][type]

        if type == 'ansi':
            codes = []
            if fg is not None:
                if 'b' in fg:
                    codes.append('1')
                    fg = fg.replace('b', '')
                codes.append('3' + fg)

            if bg is not None:
                if 'b' in bg:
                    bg = bg.replace('b', '')
                codes.append('4' + bg)

            return '\x1B[%sm' % ';'.join(codes)

        elif type == 'mirc':
            codes = []
            if fg is None:
                codes.append('')
            else:
                codes.append(fg)

            if bg is not None:
                codes.append(bg)

            out = '\x03%s' % ','.join(codes)
            if char.isdigit():
                out += '\x16\x16'

            return out

        elif type == 'html':
            codes = []
            if fg is not None:
                codes.append('color:' + fg)
            if bg is not None:
                codes.append('background-color:' + bg)

            return '<span style="%s">' % ';'.join(codes)

    def reset(self, type=None):
        if type is None: type = self.type
        if type == 'ansi':
            return '\x1B[0m'
        elif type == 'mirc':
            return '\x0F'
        elif type == 'html':
            return '</span>'

    def rainbow(self, text=None, offset=None, style='rainbow', bg=None, colorWhitespace=False):
        if text is None: return
        if offset is None:
            try: offset = self.rainbowOffset[style]
            except KeyError: offset = 0

        try:
            colmap = self.rainbowmap[style]
        except KeyError:
            raise UnknownRainbowStyle, 'style must be one of: %s' % ', '.join(self.rainbowStyles)

        output = ''
        for line in text.splitlines():
            i = 0
            for char in line:
                if colorWhitespace is False and char.isspace():
                    output += char
                else:
                    color = colmap[(offset + i) % len(colmap)]
                    output += self.getColor(fg=color, bg=bg, char=char) + char

                i += 1

            offset += 1
            output += '\n'

        self.rainbowOffset[style] = offset % 256
        return output


