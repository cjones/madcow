"""Generic shared utility methods"""

import functools
import datetime
import binascii
import tempfile
import logging
import errno
import sys
import os

class DisableAutoTimestamps(object):

    def __init__(self, *models):
        self.models = models
        self.old_values = None

    def __enter__(self):
        self.old_values = {}
        for model in self.models:
            for field in model._meta.fields:
                try:
                    self.old_values[(model, field.name)] = field.auto_now_add, field.auto_now
                except AttributeError:
                    continue
                field.auto_now_add = field.auto_now = False
        return self

    def __exit__(self, *exc_info):
        for key, values in self.old_values.iteritems():
            model, field_name = key
            auto_now_add, auto_now = values
            for field in model._meta.fields:
                if field.name == field_name:
                    field.auto_now_add = auto_now_add
                    field.auto_now = auto_now
        self.old_values = None


class TrapError(StandardError):

    """Raised if TrapError encounters an exception other than those we wish to not catch"""


class TrapErrors(object):

    """Context manager to catch all exceptions it is safe to fully trap"""

    DO_NOT_TRAP = SystemExit, KeyboardInterrupt, EOFError

    def __init__(self, reraise=True, notrap=None):
        self.reraise = reraise
        self.notrap = list(self.DO_NOT_TRAP)
        if notrap is not None:
            self.notrap.extend(notrap)

    def __enter__(self):
        """Enter context"""
        return self

    def __exit__(self, exc_type=None, exc_value=None, exc_traceback=None):
        """Exit context: Determine how to handle exception state"""
        if exc_value is not None and exc_type not in self.notrap:
            if self.reraise:
                raise TrapError(exc_type, exc_value, exc_traceback)
            return True


class zdict(dict):

    """Dictionary object with default value of 0"""

    __slots__ = ()

    def __missing__(self, key):
        """Returns 0 instead of raising KeyError"""
        return 0


def ipython(depth=0):
    """Embed IPython in running program"""
    from IPython.Shell import IPShellEmbed
    frame = sys._getframe(depth + 1)
    shell = IPShellEmbed(banner='Interactive mode, ^D to resume.', exit_msg='Resuming ...')
    shell(local_ns=frame.f_locals, global_ns=frame.f_globals)


def plural(count, name, s='s'):
    """Pluralize text helper"""
    return '%d %s%s' % (count, name, '' if count == 1 else s)


def get_logger(name, level=None, stream=None, append=False, dir=None,
               max_files=None, perms=None, date_format=None, record_format=None):

    from gruntle.memebot.utils import text
    from django.conf import settings

    if level is None:
        level = settings.LOG_LEVEL
    if dir is None:
        dir = settings.LOG_DIR
    if max_files is None:
        max_files = settings.LOG_MAX_FILES
    if perms is None:
        perms = settings.LOG_PERMS
    if date_format is None:
        date_format = settings.LOG_DATE_FORMAT
    if record_format is None:
        record_format = settings.LOG_RECORD_FORMAT

    if not os.path.exists(dir):
        os.makedirs(dir)

    if append:
        file = os.path.join(dir, name + '.log')
        if not os.path.exists(file):
            fd = os.open(file, tempfile._text_openflags, perms)
            os.close(fd)

    else:
        datestamp = datetime.date.today().strftime('%Y%m%d')
        fmt = '%%0%dd' % len(str(max_files - 1))
        for i in xrange(max_files):
            file = os.path.join(dir, '.'.join((name, datestamp, fmt % i, 'log')))
            with trapped:
                fd = os.open(file, tempfile._text_openflags, perms)
                os.close(fd)
                break
        else:
            raise OSError(errno.EEXIST, os.strerror(errno.EEXIST), file)

    logger = logging.Logger(binascii.hexlify(file), level=level)
    formatter = logging.Formatter(record_format, date_format)

    handler = logging.FileHandler(file, encoding=text.get_encoding())
    handler.setFormatter(formatter)
    handler.setLevel(level)
    logger.addHandler(handler)

    if stream is not None:
        handler = logging.StreamHandler(stream)
        handler.setFormatter(formatter)
        handler.setLevel(level)
        logger.addHandler(handler)

    class LogWrapper(object):

        WRAP_FUNCS = 'debug', 'info', 'warn', 'warning', 'error', 'fatal', 'critical', 'exception'

        def __getattribute__(self, key):
            wrapped_func = getattr(logger, key)
            if key in type(self).WRAP_FUNCS:

                @functools.wraps(wrapped_func)
                def wrapper_func(*args, **kwargs):
                    return wrapped_func(text.encode(text.format(*args, **kwargs)))

                return wrapper_func
            else:
                return wrapped_func

    return LogWrapper()


# default trapper that swallows errors
trapped = TrapErrors(reraise=False)
