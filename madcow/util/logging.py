"""Logging system"""

from datetime import datetime
from threading import RLock
import traceback
import codecs
import sys
import os

DEBUG, INFO, WARN, ERROR = xrange(4)
LEVELS = ['DEBUG', 'INFO', 'WARN', 'ERROR']

DEFAULT_LEVEL = INFO
DEFAULT_FORMAT = '[%(time)s] %(level)s: %(message)s'
DEFAULT_TIME_FORMAT = '%c'
DEFAULT_ENCODING = sys.getfilesystemencoding() or sys.getdefaultencoding() or 'ascii'

lock = RLock()

class LoggerError(Exception):

    def __str__(self):
        return '%s: %r' % (self.args[0], self.args[1])


class StreamHandler(object):

    def __init__(self, stream, encoding=None, level=None):
        if encoding is None:
            encoding = getattr(stream, 'encoding', None)
            if encoding is None:
                encoding = DEFAULT_ENCODING
        self.stream = stream
        self.encoding = encoding
        self.level = level

    @property
    def closed(self):
        try:
            return self.stream.closed
        except AttributeError:
            return False

    def flush(self):
        try:
            self.stream.flush()
        except AttributeError:
            pass

    def write(self, data):
        if isinstance(data, unicode):
            data = data.encode(self.encoding, 'ignore')
        self.stream.write(data)
        self.flush()

    def close(self):
        pass

    def __del__(self):
        try:
            self.close()
        except:
            pass


class FileHandler(StreamHandler):

    def __init__(self, file, encoding=None, level=None):
        if isinstance(file, basestring):
            basedir = os.path.split(file)[0]
            if not os.path.exists(basedir):
                os.makedirs(basedir)
            file = open(file, 'a')
        if not hasattr(file, 'write'):
            raise LoggerError('Invalid file type')
        super(FileHandler, self).__init__(file, encoding=encoding, level=level)

    def close(self):
        if not self.closed:
            self.stream.close()


class Logger(object):

    def __init__(self, level=None, format=None, time_format=None, encoding=None,
                 stream=None, file=None, store_errors=False, store_warnings=False):

        # get defaults
        if format is None:
            format = DEFAULT_FORMAT
        if time_format is None:
            time_format = DEFAULT_TIME_FORMAT
        if encoding is None:
            encoding = DEFAULT_ENCODING

        # validate
        level = convert_level(level)

        try:
            if 'MUST_EXIST' not in format % {'message': 'MUST_EXIST', 'time': None, 'level': None}:
                raise LoggerError('No message in format string', format, None)
        except (KeyError, TypeError), error:
            raise LoggerError('Invalid format', format, error)

        try:
            encoding = codecs.lookup(encoding).name
        except LookupError, error:
            raise LoggerError('Invalid encoding', encoding, error)

        # initialize
        self.level = level
        self.format = format
        self.time_format = time_format
        self.encoding = encoding
        self.store_errors = store_errors
        self.store_warnings = store_warnings

        self.level_count = dict.fromkeys(LEVELS + ['UNKNOWN'], 0)
        self.stored_errors = []
        self.stored_warnings = []

        self.handlers = []
        if stream is not None:
            self.add_stream(stream)
        if file is not None:
            self.add_file(file)

    @property
    def level_name(self):
        try:
            return LEVELS[self.level]
        except IndexError:
            return 'UNKNOWN'

    def add_stream(self, stream, level=None):
        handler = StreamHandler(stream, level=self.level if level is None else convert_level(level))
        self.handlers.append(handler)
        return handler

    def add_file(self, file, level=None):
        handler = FileHandler(file, level=self.level if level is None else convert_level(level))
        self.handlers.append(handler)
        return handler

    def close(self):
        while self.handlers:
            self.handlers.pop().close()

    def log(self, level, message, *args):
        if isinstance(level, basestring):
            try:
                level = LEVELS.index(level)
            except:
                level = len(LEVELS)
        if level >= self.level:

            # make sure this is unicode
            if not isinstance(message, unicode):
                if not isinstance(message, str):
                    for encode in str, repr:
                        try:
                            message = encode(message)
                            break
                        except Exception, error:
                            pass
                    else:
                        message = "Couldn't convert object to string: %s" % error
                        if level < WARN:
                            level = WARN
                message = message.decode(self.encoding, 'ignore')

            # apply any format args.. try not to lose them if there is a problem
            if args:
                try:
                    message = message % args
                except:
                    try:
                        message = u'message=%r, args=%r' % (message, args)
                    except:
                        pass

            try:
                level_name = LEVELS[level]
            except IndexError:
                level_name = 'UNKNOWN'

            self.level_count[level_name] += 1

            # make multi-line timestamped so stuff lines up regularly
            for line in message.splitlines():
                line = line.rstrip()
                if line:
                    opts = {'message': line, 'time': datetime.now().strftime(self.time_format), 'level': level_name}
                    line = self.format % opts
                    for handler in self.handlers:
                        if level >= handler.level:
                            with lock:
                                handler.write(line + '\n')
                    if self.store_errors and level_name == 'ERROR':
                        self.stored_errors.append(line)
                    if self.store_warnings and level_name == 'WARN':
                        self.stored_warnings.append(line)

    def debug(self, message, *args):
        self.log(DEBUG, message, *args)

    def info(self, message, *args):
        self.log(INFO, message, *args)

    def warn(self, message, *args):
        self.log(WARN, message, *args)

    warning = warn

    def error(self, message, *args):
        self.log(ERROR, message, *args)

    def exception(self, *args, **kwargs):
        exc_info = kwargs.pop('exc_info', None)
        if exc_info is None:
            exc_info = sys.exc_info()
        if args:
            self.error(*args)
        if exc_info[0] is not None:
            self.error(''.join(traceback.format_exception(*exc_info)))

    def get_named_logger(self, name):
        """Returns a wrapped logger that prefixes its messages with the given name"""
        log = type('Logger', (Logger,), {
            '__init__': lambda log_cls, *args, **kwargs: None,
            'log': lambda log, level, message, *args: self.log(level, '[%s] %s' % (name, message), *args)})()
        log.__dict__ = self.__dict__
        return log

    def setLevel(self, level):
        pass

    @property
    def file(self):
        """Convenience method to get path to file"""
        for handler in self.handlers:
            if isinstance(handler, FileHandler):
                return handler.stream.name


def convert_level(level):
    if level is None:
        level = DEFAULT_LEVEL
    try:
        if isinstance(level, basestring):
            level = LEVELS.index(level)
        else:
            if level < 0 or level >= len(LEVELS):
                raise ValueError('Out of range')
    except (IndexError, ValueError), error:
        raise LoggerError('Invalid level', level, error)
    return level


root = Logger()
debug = root.debug
info = root.info
warn = root.warn
error = root.error
exception = root.exception
