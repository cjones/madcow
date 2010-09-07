#!/usr/bin/env python
#
# Copyright (C) 2007 Christopher Jones <cjones@insub.org>
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or (at
# your option) any later version.
# 
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA

"""Python FIGlet adaption"""

import sys
import os
import re
from zipfile import ZipFile
from optparse import OptionParser

__version__ = '0.5'

class FigletError(Exception):

    def __init__(self, error):
        self.error = error

    def __str__(self):
        return str(self.error)


class FontNotFound(FigletError):

    """Raised when a font can't be located"""


class FontError(FigletError):

    """Raised when there is a problem parsing a font file"""


class FigletFont(object):

    """
    This class represents the currently loaded font, including
    meta-data about how it should be displayed by default
    """

    magic_re = re.compile(r'^[ft]lf2.')
    end_marker_re = re.compile(r'(.)\s*$')

    def __init__(self, dir='.', font='standard'):
        self.dir = dir
        self.font_name = font
        self.comment = ''
        self.chars = {}
        self.width = {}
        self.data = None
        self.read_font_file()
        self.load_font()

    def read_font_file(self):
        """
        Load font file into memory. This can be overriden with
        a superclass to create different font sources.
        """
        for ext in 'flf', 'tlf':
            font_path = '%s/%s.%s' % (self.dir, self.font_name, ext)
            if os.path.exists(font_path):
                break
        else:
            raise FontNotFound("%s doesn't exist" % font_path)
        with open(font_path, 'rb') as fp:
            self.data = fp.read()

    def get_fonts(self):
        return [filename[:-4] for filename in os.listdir(self.dir) if font.endswith('.flf') or font.endswith('.tlf')]

    def load_font(self):
        """Parse loaded font data for the rendering engine to consume"""
        try:
            self._load_font()
        except Exception, error:
            raise FontError('problem parsing %s font: %s' % (self.font_name, error))

    def _load_font(self):
        data = self.data.splitlines()
        header = data.pop(0)
        if self.magic_re.search(header) is None:
            raise FontError('%s is not a valid figlet font' % self.font_name)
        header = self.magic_re.sub('', header)
        header = header.split()
        if len(header) < 6:
            raise FontError('malformed header for %s' % self.font_name)
        hard_blank = header[0]
        height, base_line, max_len, old_layout, comment_lines = [int(_) for _ in header[1:6]]
        print_dir = full_layout = code_tag_count = None

        # these are all optional for backwards compat
        if len(header) > 6:
            print_dir = int(header[6])
        if len(header) > 7:
            full_layout = int(header[7])
        if len(header) > 8:
            code_tag_count = int(header[8])

        # if the new layout style isn't available,
        # convert old layout style. backwards compatability
        if full_layout is None:
            if old_layout == 0:
                full_layout = 64
            elif old_layout < 0:
                full_layout = 0
            else:
                full_layout = (old_layout & 31) | 128

        # Some header information is stored for later, the rendering
        # engine needs to know this stuff.
        self.height = height
        self.hard_blank = hard_blank
        self.print_dir = print_dir
        self.smush_mode = full_layout

        # Strip out comment lines
        for i in xrange(comment_lines):
            self.comment += data.pop(0)

        # Load characters
        for i in xrange(32, 127):
            end = None
            width = 0
            chars = []
            for j in xrange(height):
                line = data.pop(0)
                if end is None:
                    end = self.end_marker_re.search(line).group(1)
                    end = re.compile(re.escape(end) + r'{1,2}$')
                line = end.sub('', line)
                if len(line) > width:
                    width = len(line)
                chars.append(line)
            if ''.join(chars) != '':
                self.chars[i] = chars
                self.width[i] = width

    def __str__(self):
        return '<FigletFont object: %s>' % self.font_name


class FigletString(str):

    """Rendered figlet font"""

    # translation map for reversing ascii art / -> \, etc.
    _reverse_map = '\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f !"#$%&\')(*+,-.\\0123456789:;>=<?@ABCDEFGHIJKLMNOPQRSTUVWXYZ]/[^_`abcdefghijklmnopqrstuvwxyz}|{~\x7f\x80\x81\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x8b\x8c\x8d\x8e\x8f\x90\x91\x92\x93\x94\x95\x96\x97\x98\x99\x9a\x9b\x9c\x9d\x9e\x9f\xa0\xa1\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xab\xac\xad\xae\xaf\xb0\xb1\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xbb\xbc\xbd\xbe\xbf\xc0\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xcb\xcc\xcd\xce\xcf\xd0\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xdb\xdc\xdd\xde\xdf\xe0\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xeb\xec\xed\xee\xef\xf0\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xfb\xfc\xfd\xfe\xff'

    # translation map for flipping ascii art ^ -> v, etc.
    _flip_map = '\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f !"#$%&\'()*+,-.\\0123456789:;<=>?@VBCDEFGHIJKLWNObQbSTUAMXYZ[/]v-`aPcdefghijklwnopqrstu^mxyz{|}~\x7f\x80\x81\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x8b\x8c\x8d\x8e\x8f\x90\x91\x92\x93\x94\x95\x96\x97\x98\x99\x9a\x9b\x9c\x9d\x9e\x9f\xa0\xa1\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xab\xac\xad\xae\xaf\xb0\xb1\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xbb\xbc\xbd\xbe\xbf\xc0\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xcb\xcc\xcd\xce\xcf\xd0\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xdb\xdc\xdd\xde\xdf\xe0\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xeb\xec\xed\xee\xef\xf0\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xfb\xfc\xfd\xfe\xff'

    def reverse(self):
        return self._new_from_list([row.translate(self._reverse_map)[::-1] for row in self.splitlines()])

    def flip(self):
        return self._new_from_list([row.translate(self._flip_map) for row in self.splitlines()[::-1]])


    def _new_from_list(self, list):
        return FigletString('\n'.join(list) + '\n')


class ZippedFigletFont(FigletFont):

    """Use this Font class if it exists inside of a zipfile. """

    def __init__(self, *args, **kwargs):
        zipfile = kwargs.pop('zipfile', None)
        if zipfile is None:
            zipfile = DEFAULT_ZIPFILE
        self.zipfile = zipfile
        super(ZippedFigletFont, self).__init__(*args, **kwargs)

    def read_font_file(self):
        if not os.path.exists(self.zipfile):
            raise FontNotFound("%s doesn't exist" % self.zipfile)
        for ext in 'flf', 'tlf':
            font_path = os.path.join('fonts', '%s.%s' % (self.font_name, ext))
            try:
                self.data = ZipFile(self.zipfile, 'r').read(font_path)
                break
            except:
                pass
        else:
            raise FontNotFound(self.cont)

    def get_fonts(self):
        if not os.path.exists(self.zipfile):
            raise FontNotFound("%s doesn't exist" % self.zipfile)
        return [font[6:-4] for font in ZipFile(self.zipfile, 'r').namelist()
                if font.endswith('.flf') or font.endswith('.tlf')]


class FigletRenderingEngine(object):

    """
    This class handles the rendering of a FigletFont,
    including smushing/kerning/justification/direction
    """

    # constants.. lifted from figlet222
    SM_EQUAL = 1    # smush equal chars (not hardblanks)
    SM_LOWLINE = 2    # smush _ with any char in hierarchy
    SM_HIERARCHY = 4    # hierarchy: |, /\, [], {}, (), <>
    SM_PAIR = 8    # hierarchy: [ + ] -> |, { + } -> |, ( + ) -> |
    SM_BIGX = 16    # / + \ -> X, > + < -> X
    SM_HARDBLANK = 32    # hardblank + hardblank -> hardblank
    SM_KERN = 64
    SM_SMUSH = 128

    def __init__(self, base=None):
        self.base = base

    def smush_chars(self, left='', right=''):
        """
        Given 2 characters which represent the edges rendered figlet
        fonts where they would touch, see if they can be smushed together.
        Returns None if this cannot or should not be done.
        """
        if left.isspace():
            return right
        if right.isspace():
            return left

        # Disallows overlapping if previous or current char has a width of 1 or zero
        if (self.prev_char_width < 2) or (self.cur_char_width < 2):
            return

        # kerning only
        if (self.base.font.smush_mode & self.SM_SMUSH) == 0:
            return

        # smushing by universal overlapping
        if (self.base.font.smush_mode & 63) == 0:
            # Ensure preference to visiable characters.
            if left == self.base.font.hard_blank:
                return right
            if right == self.base.font.hard_blank:
                return left

            # Ensures that the dominant (foreground)
            # fig-character for overlapping is the latter in the
            # user's text, not necessarily the rightmost character.
            if self.base.direction == 'right-to-left':
                return left
            else:
                return right

        if ((self.base.font.smush_mode & self.SM_HARDBLANK) and
            (left == self.base.font.hard_blank) and
            (right == self.base.font.hard_blank)):
            return left
        if left == self.base.font.hard_blank or right == self.base.font.hard_blank:
            return
        if (self.base.font.smush_mode & self.SM_EQUAL) and left == right:
            return left

        if self.base.font.smush_mode & self.SM_LOWLINE:
            if (left  == '_') and (right in r'|/\[]{}()<>'):
                return right
            if (right == '_') and (left  in r'|/\[]{}()<>'):
                return left

        if self.base.font.smush_mode & self.SM_HIERARCHY:
         if (left == '|') and (right in r'|/\[]{}()<>'):
             return right
         if (right == '|') and (left in r'|/\[]{}()<>'):
             return left
         if (left in r'\/') and (right in '[]{}()<>'):
             return right
         if (right in r'\/') and (left in '[]{}()<>'):
             return left
         if (left in '[]') and (right in '{}()<>'):
             return right
         if (right in '[]') and (left in '{}()<>'):
             return left
         if (left in '{}') and (right in '()<>'):
             return right
         if (right in '{}') and (left in '()<>'):
             return left
         if (left in '()') and (right in '<>'):
             return right
         if (right in '()') and (left in '<>'):
             return left

        if self.base.font.smush_mode & self.SM_PAIR:
            for pair in [left + right, right + left]:
                if pair in ('[]', '{}', '()'):
                    return '|'

        if self.base.font.smush_mode & self.SM_BIGX:
            if (left == '/') and (right == '\\'):
                return '|'
            if (right == '/') and (left == '\\'):
                return 'Y'
            if (left == '>') and (right == '<'):
                return 'X'

    def smush_amount(self, left=None, right=None, buffer=[], cur_char=[]):
        """
        Calculate the amount of smushing we can do between this char and the last
        If this is the first char it will throw a series of exceptions which
        are caught and cause appropriate values to be set for later.

        This differs from C figlet which will just get bogus values from
        memory and then discard them after.
        """
        if (self.base.font.smush_mode & (self.SM_SMUSH | self.SM_KERN)) == 0:
            return 0

        max_smush = self.cur_char_width
        for row in xrange(self.base.font.height):
            line_left = buffer[row]
            line_right = cur_char[row]
            if self.base.direction == 'right-to-left':
                line_left, line_right = line_right, line_left
            try:
                linebd = len(line_left.rstrip()) - 1
                if linebd < 0:
                    linebd = 0
                ch1 = line_left[linebd]
            except:
                linebd = 0
                ch1 = ''
            try:
                charbd = len(line_right) - len(line_right.lstrip())
                ch2 = line_right[charbd]
            except:
                charbd = len(line_right)
                ch2 = ''
            amt = charbd + len(line_left) - 1 - linebd
            if ch1 == '' or ch1 == ' ':
                amt += 1
            elif ch2 != '' and self.smush_chars(left=ch1, right=ch2) is not None:
                amt += 1
            if amt < max_smush:
                max_smush = amt
        return max_smush

    def render(self, text):
        """Render an ASCII text string in figlet"""
        self.cur_char_width = self.prev_char_width = 0
        buffer = []
        for c in text:
            c = ord(c)
            try:
                cur_char = self.base.font.chars[c]
            except KeyError:
                continue
            self.cur_char_width = self.base.font.width[c]
            if len(buffer) == 0:
                buffer = ['' for i in xrange(self.base.font.height)]
            max_smush = self.smush_amount(buffer=buffer, cur_char=cur_char)

            # Add a character to the buffer and do smushing/kerning
            for row in xrange(self.base.font.height):
                add_left = buffer[row]
                add_right = cur_char[row]
                if self.base.direction == 'right-to-left':
                    add_left, add_right = add_right, add_left
                for i in xrange(max_smush):
                    try:
                        left = add_left[len(add_left) - max_smush + i]
                    except:
                        left = ''
                    right = add_right[i]
                    smushed = self.smush_chars(left=left, right=right)
                    try:
                        l = list(add_left)
                        l[len(l)-max_smush+i] = smushed
                        add_left = ''.join(l)
                    except:
                        pass
                buffer[row] = add_left + add_right[max_smush:]
            self.prev_char_width = self.cur_char_width

        # Justify text. This does not use str.rjust/str.center
        # specifically because the output would not match FIGlet
        if self.base.justify == 'right':
            for row in xrange(self.base.font.height):
                buffer[row] = (' ' * (self.base.width - len(buffer[row]) - 1)) + buffer[row]
        elif self.base.justify == 'center':
            for row in xrange(self.base.font.height):
                buffer[row] = (' ' * int((self.base.width - len(buffer[row])) / 2)) + buffer[row]

        # return rendered ASCII with hardblanks replaced
        buffer = '\n'.join(buffer) + '\n'
        buffer = buffer.replace(self.base.font.hard_blank, ' ')
        return FigletString(buffer)


class Figlet(object):

    """Main figlet class."""

    def __init__(self, dir=None, zipfile=None, font='standard', direction='auto', justify='auto', width=80):
        self.dir = dir
        self.font_name = font
        self._direction = direction
        self._justify = justify
        self.width = width
        self.zipfile = zipfile
        self.set_font()
        self.engine = FigletRenderingEngine(base=self)

    def set_font(self, dir=None, font_name=None, zipfile=None):
        if dir is not None:
            self.dir = dir
        if font_name is not None:
            self.font_name = font_name
        if zipfile is not None:
            self.zipfile = zipfile
        font = None
        if self.zipfile:
            try:
                font = ZippedFigletFont(dir=self.dir, font=self.font_name, zipfile=self.zipfile)
            except:
                pass
        if font is None and self.dir:
            try:
                font = FigletFont(dir=self.dir, font=self.font_name)
            except:
                pass
        if font is None:
            raise FontNotFound("Couldn't load font %s: Not found" % self.font_name)
        self.font = font

    @property
    def direction(self):
        if self._direction == 'auto':
            direction = self.font.print_dir
            if direction == 0:
                return 'left-to-right'
            elif direction == 1:
                return 'right-to-left'
            else:
                return 'left-to-right'
        else:
            return self._direction

    @property
    def justify(self):
        if self._justify == 'auto':
            if self.direction == 'left-to-right':
                return 'left'
            elif self.direction == 'right-to-left':
                return 'right'
        else:
            return self._justify

    def render_text(self, text):
        """wrapper method to engine"""
        return self.engine.render(text)

    def get_fonts(self):
        return self.font.get_fonts()


def main(argv=None):
    dir = os.path.realpath(os.path.dirname(__file__))
    parser = OptionParser(version=__version__, usage='%prog [options] text..')
    parser.add_option('-f', '--font', default='standard',
                      help='font to render with (default: %default)', metavar='FONT' )
    parser.add_option('-d', '--fontdir', default='/usr/share/figlet',
                      help='location of font files', metavar='DIR' )
    parser.add_option('-z', '--zipfile', default=dir+'/fonts.zip',
                      help='specify a zipfile to use instead of a directory of fonts' )
    parser.add_option('-D', '--direction', type='choice', choices=('auto', 'left-to-right', 'right-to-left'),
                      default='auto', metavar='DIRECTION',
                      help='set direction text will be formatted in (default: %default)' )
    parser.add_option('-j', '--justify', type='choice', choices=('auto', 'left', 'center', 'right'),
                      default='auto', metavar='SIDE',
                      help='set justification, defaults to print direction' )
    parser.add_option('-w', '--width', type='int', default=80, metavar='COLS',
                      help='set terminal width for wrapping/justification (default: %default)' )
    parser.add_option('-r', '--reverse', action='store_true', default=False,
                      help='shows mirror image of output text' )
    parser.add_option('-F', '--flip', action='store_true', default=False,
                      help='flips rendered output text over' )
    opts, args = parser.parse_args(argv)
    if not args:
        parser.print_help()
        return 2
    text = ' '.join(args)
    figlet = Figlet(dir=opts.fontdir, font=opts.font, direction=opts.direction,
                    justify=opts.justify, width=opts.width, zipfile=opts.zipfile)

    text = figlet.render_text(text)
    if opts.reverse:
        text = text.reverse()
    if opts.flip:
        text = text.flip()
    print text
    return 0

if __name__ == '__main__':
    sys.exit(main())
