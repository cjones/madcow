"""Utility functions for unicode handling"""

import codecs
import sys

from gruntle.memebot.utils import zdict
from gruntle.memebot.exceptions import *

__all__ = ['get_encoding', 'set_encoding', 'encode', 'decode', 'sencode', 'sdecode', 'cast', 'chomp', 'format']

# defaults
DEFAULT_AUTO_ENCODINGS = 'ascii', 'utf-8', 'latin1'
DEFAULT_FAILBACK_ENCODING = 'ascii'
DEFAULT_CHOMP_CHARS = '\r', '\n'
DEFAULT_CAST_TYPES = int, float

class EncodingHandler(object):

    """Manages encoding detection and provides conversion functions"""

    def __init__(self, preferred_encoding=None,
                       extra_auto_encodings=None,
                       auto_encodings=None,
                       failback_encoding=None,
                       chomp_chars=None,
                       cast_types=None):

        """
        Construct new handler instance:

        preferred_encoding      - (str) Encoding to try before auto-detection gives it a shot
        extra_auto_encodings    - (seq) Encodings to try if auto-detection also failed
        auto_encodings          - (seq) Primary encodings to use for auto-detection
        default_encoding        - (str) Failback encoding for extreme failure coditions
        chomp_chars             - (seq) Characters to remove from end of line when using chomp()
        cast_types              - (seq) Sequence of type objects to use when attempting coersion
        """

        # get defaults if none provided
        if auto_encodings is None:
            auto_encodings = DEFAULT_AUTO_ENCODINGS
        if failback_encoding is None:
            failback_encoding = DEFAULT_FAILBACK_ENCODING
        if chomp_chars is None:
            chomp_chars = DEFAULT_CHOMP_CHARS
        if cast_types is None:
            cast_types = DEFAULT_CAST_TYPES

        # store attributes
        self.preferred_encoding = preferred_encoding
        self.extra_auto_encodings = extra_auto_encodings
        self.auto_encodings = auto_encodings
        self.failback_encoding = failback_encoding
        self.chomp_chars = chomp_chars
        self.cast_types = cast_types

        # initialize cache
        self._system_encoding = None

    def set_encoding(self, encoding=None):
        """Sets the preferred encoding for this handler"""
        if encoding is None:
            preferred_encoding = None
        else:
            preferred_encoding = self.check_encoding(encoding)
            if preferred_encoding is None:
                raise LookupError('unknown encoding: %s' % (self.encode(encoding)))
        self.preferred_encoding = preferred_encoding

    def get_encoding(self):
        """Returns this handler's preferred encoding"""
        for encoding in self.preferred_encoding, self.system_encoding:
            encoding = self.check_encoding(encoding)
            if encoding is not None:
                return encoding
        return self.failback_encoding

    encoding = property(get_encoding)

    @property
    def system_encoding(self):
        """Encoding the system is configured to use"""
        if self._system_encoding is None:
            self._system_encoding = self.autodetect_system_encoding()
        if self._system_encoding is None:
            return self.failback_encoding
        return self._system_encoding

    def autodetect_system_encoding(self):
        """Returns most likely system encoding"""
        candidates = zdict()
        for get_encoding in (sys.getfilesystemencoding,
                             sys.getdefaultencoding,
                             lambda: sys.stdin.encoding,
                             lambda: sys.stdout.encoding,
                             lambda: sys.stderr.encoding,
                             lambda: self.failback_encoding):
            with trapped:
                encoding = get_encoding()
                encoding = self.check_encoding(encoding)
                candidates[encoding] += 1
        if candidates:
            return max(candidates, key=lambda encoding: candidates[encoding])
        return self.failback_encoding

    def get_encodings(self, requested_encoding=None):
        """Return list candidate encodings/error handlers to use for encode/decode"""
        encodings = [requested_encoding, self.preferred_encoding, self.system_encoding]
        encodings.extend(self.auto_encodings)
        if self.extra_auto_encodings is not None:
            encodings.extend(self.extra_auto_encodings)
        encodings = (self.check_encoding(encoding) for encoding in encodings)
        encodings = [(encoding, 'strict') for encoding in encodings if encoding is not None]
        encodings.append((self.failback_encoding, 'replace'))
        return sorted(set(encodings), key=lambda arg: encodings.index(arg))

    def recode(self, recode_func, requested_encoding, return_type):
        """Wrapper to safely encode/decode object"""
        for recode_args in self.get_encodings(requested_encoding):
            with trapped:
                return recode_func(*recode_args)
        return return_type()

    def decode(self, val, encoding=None):
        """Decode val to unicode, violently if necessary"""
        if val is None:
            val = u''
        elif not isinstance(val, unicode):
            if not isinstance(val, str):
                try:
                    with TrapErrors():
                        val = str(val)
                except TrapError:
                    val = ''
            val = self.recode(val.decode, encoding, unicode)
        return val

    def encode(self, val, encoding=None):
        """Encode val to byte stream, violently if necessary"""
        val = self.decode(val, encoding)
        return self.recode(val.encode, encoding, str)

    def sdecode(self, val, encoding=None):
        """Decode and strip whitespace, None if empty"""
        val = self.decode(val, encoding).strip()
        if val:
            return val

    def sencode(self, val, encoding=None):
        """Encode and strip whitespace, None if empty"""
        val = self.encode(val, encoding).strip()
        if val:
            return val

    def chomp(self, line, encoding=None):
        """Remove any trailing newline/linefeed characters"""
        return_unicode = isinstance(line, unicode)
        line = self.encode(line, encoding)
        chars = list(line)
        while chars and chars[-1] in self.chomp_chars:
            chars.pop()
        line = ''.join(chars)
        if return_unicode:
            return self.decode(line, encoding)
        return line

    def cast(self, val, encoding=None):
        """Attempt to coerce a reasonable primitive data type for val"""
        val = self.sencode(val, encoding)
        if val is not None:
            for cast_type in self.cast_types:
                with trapped:
                    return cast_type(val)
        return self.sdecode(val, encoding)

    def format(self, format, *args, **kwargs):
        """Encoding-aware string formatting"""
        encoding = kwargs.pop('encoding', None)
        objs = [format]
        if args:
            objs.extend(args)
        if kwargs:
            objs.extend(kwargs.iteritems())
        recode = self.decode if (unicode in set(type(obj) for obj in objs)) else self.encode
        if args:
            args = tuple(recode(arg, encoding) if isinstance(arg, (str, unicode)) else arg for arg in args)
        if kwargs:
            kwargs = dict((self.encode(key, encoding),
                           recode(val, encoding) if isinstance(val, (str, unicode)) else val)
                          for key, val in kwargs.iteritems())
        format = recode(format, encoding)
        for opts in args, kwargs:
            if opts:
                try:
                    with TrapErrors():
                        format = format % opts
                except TrapError, exc:
                    with trapped:
                        format = recode('Error: %r %% %r -> %r' % (format, opts, exc.args[1]), encoding)
        return format

    @staticmethod
    def check_encoding(encoding):
        """Verify encoding is valid, returns normalized name or None if invalid"""
        with trapped:
            return codecs.lookup(encoding).name

    @classmethod
    def export_methods(cls, methods, *args, **kwargs):
        """Create default handler and export methods into global namespace, takes same options as constructor"""
        handler = cls(*args, **kwargs)
        context = globals()
        for key in methods:
            if key not in context:
                val = getattr(handler, key, None)
                if val is not None:
                    context[key] = val


EncodingHandler.export_methods(__all__)
