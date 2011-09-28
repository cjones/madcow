"""MemeBot exceptions"""

import re

__all__ = ['MemebotError', 'OldMeme', 'ScannerError', 'BadResponse', 'ConfigError', 'InvalidContent',
           'NoMatch', 'LockError', 'TrapError', 'TrapErrors', 'trapped', 'reraise']

class MemebotError(StandardError):

    """Base error class for memebot"""


class OldMeme(MemebotError):

    """Raised when a URL is reposted public"""

    def __init__(self, link):
        self.link = link

    def __str__(self):
        return 'Oldest meme EVAR! %r' % self.link


class ScannerError(MemebotError):

    """Base scanner exception"""


class BadResponse(ScannerError):

    """Raised if response was not OK"""

    def __init__(self, link, response):
        self.link = link
        self.response = response

    @property
    def fatal(self):
        """True if this error should signal the doom of this link despite its error count"""
        return self.response.code == 404

    def __str__(self):
        from gruntle.memebot.utils.text import encode, format
        return encode(format('%s rsponded with status: %d %s', self.link.url, self.response.code, self.response.msg))


class ConfigError(ScannerError):

    """Scanner is improperly configured"""


class InvalidContent(ScannerError):

    """Raised if scanner does not like the content it is trying to render"""

    def __init__(self, response, msg=None):
        self.response = response
        self.msg = msg

    def __str__(self):
        from gruntle.memebot.utils.text import encode, format
        return encode(format('Invalid content parsing %s: %s', self.response.url,
                             'Unknown error' if self.msg is None else self.msg))


class NoMatch(ScannerError):

    """Raised when scanner doesn't match"""

    def __init__(self, url, field, val, regex, regex2=None):
        self.url = url
        self.field = field
        self.val = val
        self.regex = regex
        self.regex2 = regex2

    @staticmethod
    def get_re_flags():
        """Yields name/value of re.py's flags"""
        for key in dir(re):
            val = getattr(re, key)
            if key.isupper() and isinstance(val, (int, long)) and not key.startswith('_') and len(key) > 1:
                yield key, val

    @property
    def pattern(self):
        """Retrieve the pattern for compile regex from re.py's cache"""
        for key, val in re._cache.iteritems():
            if val is self.regex:
                return key[1], [name for name, val in self.get_re_flags() if key[2] & val]
        return 'UNKNOWN', []

    def __str__(self):
        from gruntle.memebot.utils.text import encode, format
        pattern, flags = self.pattern
        return encode(format('No match (%s): %s %r != %r [%s]',
                             self.url, self.field, self.val,
                             pattern, ', '.join(flags)))


class LockError(MemebotError):

    """Raised when locking mechanism encounters a problem"""


class TrapError(MemebotError):

    """Raised if TrapError encounters an exception other than those we wish to not catch"""


class TrapErrors(object):

    """Context manager to catch all exceptions it is safe to fully trap"""

    DO_NOT_TRAP = SystemExit, KeyboardInterrupt, EOFError

    def __init__(self, reraise=True, ignore=None):
        self.reraise = reraise
        self.ignore = list(self.DO_NOT_TRAP)
        if ignore is not None:
            if isinstance(ignore, Exception):
                ignore = [ignore]
            self.ignore.extend(ignore)

    def __enter__(self):
        """Enter context"""
        return self

    def __exit__(self, exc_type=None, exc_value=None, exc_traceback=None):
        """Exit context: Determine how to handle exception state"""
        if exc_value is not None and exc_type not in self.ignore:
            if self.reraise:
                raise TrapError(exc_type, exc_value, exc_traceback)
            return True


def reraise(exc_type, exc_value, exc_traceback):
    """Lazy-ass shortcut so I can write reraise(*exc_info)"""
    raise exc_type, exc_value, exc_traceback


# default trapper that swallows errors
trapped = TrapErrors(reraise=False)
