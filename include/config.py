from __future__ import with_statement
from ConfigParser import ConfigParser
import logging as log
import sys
import os
import re

ENCODING = sys.getfilesystemencoding()

class ConfigSection(object):

    def __init__(self, options):
        self.__dict__.update(options)

    def __iter__(self):
        for key, val in self.__dict__.iteritems():
            yield key, val

    def __getattribute__(self, key):
        return super(ConfigSection, self).__getattribute__(key.lower())


class Config(object):

    isint_re = re.compile(r'^-?[0-9]+$')
    isfloat_re = re.compile(r'^\s*-?(?:\d+\.\d*|\d*\.\d+)\s*$')
    istrue_re = re.compile(u'^(?:true|yes|on)$', re.I)
    isfalse_re = re.compile(u'^(?:false|no|off)$', re.I)

    def __init__(self, settings, defaults):
        self._settings_file = settings
        self._defaults_file = defaults
        self._defaults = self.parse(defaults)
        self._settings = self.parse(settings)
        for name, options in self._defaults.iteritems():
            if name not in self._settings:
                log.info('missing: %s, using defaults' % name)
                self._settings[name] = options
                continue
            for key, val in options.iteritems():
                if key not in self._settings[name]:
                    self._settings[name][key] = val
                    log.info('missing: %s.%s, using default (%r)' % (
                        name, key, val))
        for name, options in self._settings.iteritems():
            setattr(self, name, ConfigSection(options))

    @classmethod
    def parse(cls, file):
        parser = ConfigParser()
        parser.read(file)
        data = {}
        for section in parser.sections():
            for key, val in parser.items(section):
                if cls.isint_re.search(val):
                    val = int(val)
                elif cls.isfloat_re.search(val):
                    val = float(val)
                elif cls.istrue_re.search(val):
                    val = True
                elif cls.isfalse_re.search(val):
                    val = False
                data.setdefault(section.lower(), {})[key] = val
        return data

    def save(self, filename=None):
        if filename is None:
            filename = self._settings_file
        config = ConfigParser()
        for section, options in self._settings.iteritems():
            for key, val in options.iteritems():
                if (section in self._defaults and
                    key in self._defaults[section] and
                    val != self._defaults[section][key]):
                    if isinstance(val, bool):
                        val = 'yes' if val else 'no'
                    if not isinstance(val, basestring):
                        val = str(val)
                    if isinstance(val, unicode):
                        val = val.encode(ENCODING)
                    if not config.has_section(section):
                        config.add_section(section)
                    config.set(section, key, val)

        if os.path.exists(filename):
            os.rename(filename, filename + '.bak')
        with open(filename, 'wb') as fp:
            config.write(fp)
        log.info('wrote settings to ' + filename)

    def __getattribute__(self, key):
        return super(Config, self).__getattribute__(key.lower())

