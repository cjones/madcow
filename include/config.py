from ConfigParser import ConfigParser
import logging as log
import re

class ConfigSection(object):

    def __init__(self, options):
        self.__dict__.update(options)

    def __iter__(self):
        for key, val in self.__dict__.iteritems():
            yield key, val


class Config(object):

    isint_re = re.compile(r'^-?[0-9]+$')
    isfloat_re = re.compile(r'^\s*-?(?:\d+\.\d*|\d*\.\d+)\s*$')
    istrue_re = re.compile(u'^(?:true|yes|on)$', re.I)
    isfalse_re = re.compile(u'^(?:false|no|off)$', re.I)

    def __init__(self, settings, defaults):
        defaults = self.parse(defaults)
        settings = self.parse(settings)
        for name, options in defaults.iteritems():
            if name not in settings:
                log.warn('missing: %s, using defaults' % name)
                settings[name] = options
                continue
            for key, val in options.iteritems():
                if key not in settings[name]:
                    settings[name][key] = val
                    log.warn('missing: %s.%s, using default (%r)' % (
                        name, key, val))
        for name, options in settings.iteritems():
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
