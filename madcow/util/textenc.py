"""
Try to hide as much unicode-related nastiness as possible. encode() and decode() will
take *anything* and always return a string and unicode, respectively, by cycling through
a series of common encodings until something works, ultimately failing back to 7bit ascii
with errors replaced by "?". If this approach seriously fails, it'll issue a warning and
return an empty string.  Order of encodings attempted:

$requested_encoding     - optionally provided when encode() or decode() is called
$preferred_encoding     - optionally set when handler is initialized
$system_encoding        - auto-detected by analyzing various system-level properties
ascii                   - called in strict mode first, if it's all 7bit chars, it's surely ascii
utf-8                   - a very common unicode format that fails easily if the text *isn't* utf-8
utf-16                  - less common, but it's out there. also fails easily without BOM
$check_encodings        - optional, a list of encodings to test before we go into failback mode
latin1                  - (aka iso8859-1) pretty common, called last because it generally can't fail
ascii (replace errors)  - if for some reason latin1 fails, this surely won't.... surely.
"""

import warnings
import codecs
import sys

CHECK_ENCODINGS = 'ascii', 'utf-8', 'utf-16'
DEFAULT_ENCODING = 'ascii'
NO_TRAP_EXCEPTIONS = SystemExit, KeyboardInterrupt

__version__ = '0.1'
__author__ = 'Chris Jones <cjones@gmail.com>'
__license__ = 'BSD'
__all__ = ['UnicodeFatality', 'UnicodeHandler', 'set_preferred_encoding', 'get_encoding', 'encode', 'decode']

class UnicodeFatality(UnicodeWarning):

    """Raised if encode/decode seriously failed"""

    message_fmt = "Couldn't %s text %r using any of the following: %s"

    def __init__(self, method, text, encodings):
        message = message_fmt % (method, text, ', '.join('%s(%s)' % args for args in encodings))
        super(UnicodeFatality, self).__init__(message)


class zdict(dict):

    """Dictionary with default value of 0"""

    __slots__ = ()
    __missing__ = lambda *_: 0


class UnicodeHandler(object):

    """Try to hide as much unicode-related nastiness as possible"""

    def __init__(self, preferred_encoding=None, extra_encodings=None):
        self.preferred_encoding = preferred_encoding
        self.extra_encodings = extra_encodings
        self._system_encoding = None

    @property
    def system_encoding(self):
        """Auto-detected system encoding"""
        if self._system_encoding is None:
            self._system_encoding = self._detect_system_encoding()
        return self._system_encoding

    def get_preferred_encoding(self):
        """Gets user-defined preferred encoding"""
        return self._preferred_encoding

    def set_preferred_encoding(self, encoding):
        """Sets user-defined preferred encoding"""
        self._preferred_encoding = self.check_encoding(encoding)

    preferred_encoding = property(get_preferred_encoding, set_preferred_encoding, doc='User-defined preferred encoding')

    def get_encoding(self, encoding=None):
        """Get encoding to use (first valid of: request -> preferred -> system -> default)"""
        encoding = self.check_encoding(encoding)
        if encoding is None:
            encoding = self.preferred_encoding
            if encoding is None:
                encoding = self.system_encoding
                if encoding is None:
                    encoding = DEFAULT_ENCODING
        return encoding

    encoding = property(get_encoding)

    @staticmethod
    def check_encoding(encoding):
        """Return real encoding name, or None if invalid"""
        if encoding is not None:
            try:
                return codecs.lookup(encoding).name
            except NO_TRAP_EXCEPTIONS:
                raise
            except:
                pass

    @classmethod
    def _detect_system_encoding(cls):
        """Check various system properties and return most likely system-level encoding"""
        candidates = zdict()
        for get_encoding in (sys.getfilesystemencoding,
                             sys.getdefaultencoding,
                             lambda: sys.stdin.encoding,
                             lambda: sys.stdout.encoding,
                             lambda: sys.stderr.encoding,
                             lambda: DEFAULT_ENCODING):
            encoding = cls.check_encoding(get_encoding())
            if encoding is not None:
                candidates[encoding] += 1
        if candidates:
            return max(candidates, key=lambda encoding: candidates[encoding])

    def get_encoding_args(self, requested_encoding=None):
        """Builds list of encodings and their error handling argument to use in encode/decode"""
        encodings = [requested_encoding, self.preferred_encoding, self.system_encoding]
        encodings.extend(CHECK_ENCODINGS)
        if self.extra_encodings:
            encodings.extend(self.extra_encodings)
        encodings.append('iso8859-1')
        encodings = (self.check_encoding(encoding) for encoding in encodings)
        return [(encoding, 'strict') for encoding in encodings if encoding] + [(DEFAULT_ENCODING, 'replace')]

    def safe_recode(self, recode_func, encoding, default=None):
        """Run the encode/decode function without blowing up"""
        encodings = self.get_encoding_args(encoding)
        for args in encodings:
            try:
                val = recode_func(*args)
                break
            except NO_TRAP_EXCEPTIONS:
                raise
            except:
                pass
        else:
            self.fatality(recode_func.func_name, val, encodings)
            val = default
        return val

    def decode(self, val, encoding=None):
        """Convert val to unicode, violently if necessary"""
        if val is None:
            val = u''
        elif not isinstance(val, unicode):
            if not isinstance(val, str):
                # not even a string! that's ok, lots of stuff can be a string if it wants to
                try:
                    val = str(val)
                except NO_TRAP_EXCEPTIONS:
                    raise
                except:
                    val = ''
            val = self.safe_recode(val.decode, encoding, u'')
        return val

    def encode(self, val, encoding=None):
        """Convert val to byte stream, violently if necessary"""
        val = self.decode(val, encoding)
        return self.safe_recode(val.encode, encoding, '')

    @staticmethod
    def fatality(*args):
        """Issue warning if encode/decode managed to fail"""
        warnings.warn(UnicodeFatality(*args), stacklevel=2)


default_handler = UnicodeHandler()

# common methods exported from default handler
set_preferred_encoding = default_handler.set_preferred_encoding
get_encoding = default_handler.get_encoding
encode = default_handler.encode
decode = default_handler.decode
