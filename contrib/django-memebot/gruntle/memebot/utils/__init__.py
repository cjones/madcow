"""Generic shared utility methods"""

import functools
import traceback
import urlparse
import datetime
import binascii
import tempfile
import logging
import decimal
import rfc822
import socket
import shutil
import errno
import time
import sys
import os
import re

class DisableAutoTimestamps(object):

    """Context manager: Disables auto_now and auto_now_add on DateTimeFields for the models specified"""

    def __init__(self, *models):
        self.models = models
        self.old_values = None

    def __enter__(self):
        """Auto-detect fields, store original value, and disable"""
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
        """Restore original value"""
        for key, values in self.old_values.iteritems():
            model, field_name = key
            auto_now_add, auto_now = values
            for field in model._meta.fields:
                if field.name == field_name:
                    field.auto_now_add = auto_now_add
                    field.auto_now = auto_now
        self.old_values = None


class zdict(dict):

    """Dictionary object with default value of 0"""

    __slots__ = ()
    __missing__ = lambda *_: 0


class AtomicWrite(object):

    """Context Manager: Safely opens existing files for atomic writing"""

    def __init__(self, file, backup=False, perms=None):
        self.file = os.path.realpath(file)
        self.backup = backup
        self.perms = perms
        self.reset()

    def reset(self):
        """Null out cached attributes of open files"""
        self.temp_file = None
        self.fd = None
        self.fp = None

    def __enter__(self):
        """Enter context: Create temporary file for writing, copying stat() of original"""
        from gruntle.memebot.exceptions import TrapErrors, TrapError, trapped, reraise

        # make sure the directory exists
        dirname, basename = os.path.split(self.file)
        if not os.path.exists(dirname):
            os.makedirs(dirname)

        # construct temporary file in the same directory as the original
        name, ext = os.path.splitext(basename)
        self.fd, self.temp_file = tempfile.mkstemp(suffix=ext, prefix='.%s-' % name, dir=dirname)

        try:
            with TrapErrors():
                exists = os.path.exists(self.file)
                if self.perms is not None:
                    os.chmod(self.file if exists else self.temp_file, self.perms)
                if exists:
                    shutil.copystat(self.file, self.temp_file)
                    if self.backup:
                        backup_file = self.file + '.bak'
                        if os.path.exists(backup_file):
                            os.remove(backup_file)
                        shutil.copy2(self.file, backup_file)
                self.fp = os.fdopen(self.fd, 'w')
        except TrapError, exc:
            with trapped:
                os.close(self.fd)
            if os.path.exists(self.temp_file):
                with trapped:
                    os.remove(self.temp_file)
            self.reset()
            reraise(*exc.args)

        return self.fp

    def __exit__(self, *exc_info):
        """Exist context: Move file into place with atomic os.rename() if no errors. Clean up cruft"""
        from gruntle.memebot.exceptions import trapped
        if exc_info[1] is None:
            os.rename(self.temp_file, self.file)
        with trapped:
            self.fp.close()
        with trapped:
            os.close(self.fd)
        if os.path.exists(self.temp_file):
            with trapped:
                os.remove(self.temp_file)
        self.reset()


class Serializable(object):

    def __key__(self):
        return make_unique_key(self.__dict__)

    def __hash__(self):
        return hash(self.__key__())

    def __eq__(self, other):
        if not isinstance(other, Serializable):
            return NotImplemented
        return hash(self) == hash(other)

    def __ne__(self, other):
        equals = self.__eq__(other)
        if equals is NotImplemented:
            return equals
        return not equals


def ipython():
    """
    Embed IPython in running program. This does a few non-standard things:

    1. Executes in caller frame's context, rather than inside this function.
    2. Prevents re-entry to help avoid difficult-to-break loops.
    3. Resets sys.argv to avoid certain errors, then restores when done.
    """
    from IPython.Shell import IPShellEmbed as s
    if not getattr(s, 'x', 0):
        a, sys.argv, f, s.x = sys.argv, [sys.argv[0]], sys._getframe(1), 1
        try:
            s()('', f.f_locals, f.f_globals)
        finally:
            sys.argv = a


def plural(count, name, s='s'):
    """Pluralize text helper"""
    return '%d %s%s' % (count, name, '' if count == 1 else s)


def get_logger(name, level=None, stream=None, append=False, dir=None,
               max_files=None, perms=None, date_format=None, record_format=None):

    """Get a named logger configured to use the site log directory"""

    from gruntle.memebot.exceptions import trapped
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

        """Add/change some functionality to stdlib's logger"""

        WRAP_FUNCS = 'debug', 'info', 'warn', 'warning', 'error', 'fatal', 'critical', 'exception'

        def __init__(self, name=None):
            self.name = name

        @property
        def prefix(self):
            if self.name:
                return text.decode(text.format('[%s] ', self.name))
            return u''

        def __getattribute__(self, key):
            try:
                return super(LogWrapper, self).__getattribute__(key)
            except AttributeError:
                wrapped_func = getattr(logger, key)
                if key in type(self).WRAP_FUNCS:

                    @functools.wraps(wrapped_func)
                    def wrapper_func(*args, **kwargs):
                        exc_info = kwargs.pop('exc_info', None)
                        output = self.prefix + text.decode(text.format(*args, **kwargs))
                        wrapped_func(output)
                        if exc_info is not None:
                            for line in traceback.format_exception(*exc_info):
                                wrapped_func(self.prefix + text.chomp(text.decode(line)))

                    return wrapper_func
                else:
                    return wrapped_func

        def get_named_logger(self, name):
            """Return named interface to this logger"""
            return type(self)(name)

    return LogWrapper()


def first(*args):
    """Like any() and all() ... except it's first(). Returns None if nothing is True"""
    if len(args) == 1 and isinstance(args[0], (tuple, list)):
        args = args[0]
    for arg in args:
        if arg:
            return arg


def get_domain():
    """Determine the domain portion of our name"""
    return re.sub('^' + re.escape('.'.join(socket.gethostname().split('.') + [''])), '', socket.getfqdn())


def get_domain_from_url(url):
    """Return normalized domain portion of the URL"""
    from gruntle.memebot.utils import text
    items = text.decode(urlparse.urlparse(url).netloc).lower().rsplit(u':', 1)[0].split(u'.')[-2:]
    return text.encode(u'.'.join(item for item in (item.strip() for item in items) if item))


def make_unique_key(object):
    """Try to hash any object, coercing type as necessary"""
    try:
        return hash(object)
    except TypeError:
        name = type(object).__name__
        if isinstance(object, dict):
            object = sorted(object.iteritems(), key=lambda item: item[0])
        elif isinstance(object, set):
            object = sorted(object)
        return hash((name, tuple(make_unique_key(item) for item in object)))


def flatten(*args, **kwargs):
    """Flattens arbitrary arguments to a single sequence"""
    return _flatten((args, kwargs))


def _flatten(items):
    """Internal to flatten()"""
    flat = []
    for item in items:
        if isinstance(item, dict):
            item = sorted(item.iteritems(), key=lambda item: item[0])
        elif isinstance(item, set):
            item = sorted(item)
        if isinstance(item, (tuple, list)):
            flat.extend(_flatten(item))
        else:
            flat.append(item)
    return flat


def iso8061time(dt=None, utc=False):
    """Format local datetime as W3CDTF/iso8061/rfc3339 (2011-10-05T15:04:33+07:00 or 2011-10-05T22:04:33Z)"""
    if dt is None:
        dt = datetime.datetime.now()
    u = datetime.datetime.utcfromtimestamp(time.mktime(dt.timetuple()))
    if utc:
        dt, z = u, 'Z'
    else:
        o = (u - dt.replace(microsecond=0)).total_seconds()
        s, f = ('-', -1) if (o < 0) else ('+', 1)
        z = s + '%02d:%02d' % divmod(o * f / 60, 60)
    return dt.isoformat().split('.', 1)[0] + z


def rfc822time(dt=None):
    """Format local datetime as rfc822 (Wed, 05 Oct 2011 22:04:33 GMT)"""
    if dt is None:
        dt = datetime.datetime.now()
    return rfc822.formatdate(time.mktime(dt.timetuple()))


def human_readable_duration(duration, precision=None):
    """
    Return human readable version of supplied duration. It may be a
    number type, indicating seconds elapsed, a timedelta object
    interpreted the same, or a date or datetime object, which will
    return the duration between then and now.

    Stting precision allows you to truncate how many units it will use
    to express the duration. For example, when using precision=2,  "40
    years, 9 months, 32 days, 7 hours, 16 minutes, and 44 seconds" would
    instead read "40 years and 9 months".
    """
    if isinstance(duration, datetime.date):
        now = datetime.datetime.now()
        if type(duration) is datetime.date:
            now = now.date()
        duration -= now
    if isinstance(duration, datetime.timedelta):
        duration = duration.total_seconds()
    duration = int(round(duration, 0))
    if duration < 0:
        duration *= -1

    parts = []
    for size, unit in ((60, 'second'),
                       (60, 'minute'),
                       (24, 'hour'),
                       (7, 'day'),
                       (4, 'week'),
                       (12, 'month'),
                       (None, 'year')):

        if size is None:
            parts.append((duration, unit))
        else:
            duration, r = divmod(duration, size)
            if r:
                parts.append((r, unit))
            if not duration:
                break

    if parts:
        parts = [plural(*part) for part in reversed(parts)]
        if precision is not None:
            parts = parts[:precision]
        hold = parts.pop()
        result = [', '.join(parts)]
        if len(parts) > 1:
            result.append(',')
        if parts:
            result.append(' and ')
        result.append(hold)
        result = ''.join(result)
    else:
        result = 'less than 1 second'
    return result
