"""Config management"""

from ConfigParser import ConfigParser
import sys
import os
import re
from madcow.util.encoding import ENCODING

isint_re = re.compile(r'^-?[0-9]+$')
isfloat_re = re.compile(r'^\s*-?(?:\d+\.\d*|\d*\.\d+)\s*$')
istrue_re = re.compile(u'^(?:true|yes|on)$', re.I)
isfalse_re = re.compile(u'^(?:false|no|off)$', re.I)

class Section(object):

    def __init__(self, values=None):
        if values is None:
            values = {}
        self.values = values

    def __getattribute__(self, key):
        try:
            val = super(Section, self).__getattribute__(key)
        except AttributeError:
            val = self.values.get(key)
            if isinstance(val, dict):
                val = Section(val)
        return val

    __getitem__ = __getattribute__


class Config(Section):

    def __init__(self, settings_file, default_settings_file=None, overrides=None, encoding=None):
        if encoding is None:
            encoding = ENCODING
        self.settings_file = settings_file
        self.default_settings_file = default_settings_file
        self.encoding = encoding
        super(Config, self).__init__()
        if default_settings_file:
            self.read_config(default_settings_file)
        self.read_config(settings_file)

    def read_config(self, file):
        parser = ConfigParser()
        parser.read(file)
        for name in parser.sections():
            for key, val in parser.items(name):
                self.values.setdefault(name, {})[key] = self.to_python(val)

    def save(self, filename=None, ignore_unchanged=False):
        if filename is None:
            filename = self.settings_file
        parser = ConfigParser()
        for section, options in self.values.iteritems():
            for key, val in options.iteritems():
                if not parser.has_section(section):
                    parser.add_section(section)
                parser.set(section, key, self.to_string(val))

        if os.path.exists(filename):
            os.rename(filename, filename + '.bak')
        with open(filename, 'wb') as fp:
            parser.write(fp)

    def to_python(self, val):
        if isinstance(val, str):
            val = val.decode(self.encoding)
        if not isinstance(val, unicode):
            raise TypeError('values from config parser should be a string')
        if isint_re.search(val):
            val = int(val)
        elif isfloat_re.search(val):
            val = float(val)
        elif istrue_re.search(val):
            val = True
        elif isfalse_re.search(val):
            val = False
        if isinstance(val, unicode) and not val:
            val = None
        return val

    def to_string(self, val):
        if val is None:
            val = u''
        elif isinstance(val, str):
            val = val.decode(self.encoding)
        elif isinstance(val, bool):
            val = u'yes' if val else u'no'
        else:
            val = unicode(val)
        return val.encode(self.encoding)
