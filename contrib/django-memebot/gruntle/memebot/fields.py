"""Custom model fields"""

import collections
import base64
import zlib
import gzip

try:
    import cStringIO as stringio
except ImportError:
    import StringIO as stringio

from django.db import models
from django.conf import settings

from gruntle.memebot.utils import text

__all__ = ['SerializedDataField']

class SerializedDataField(models.Field):

    """Field that can save arbitrary binary data, compressed and base64 encoded into a text field"""

    __metaclass__ = models.SubfieldBase

    HEADER = 'SerializedData:'
    DEFAULT_ENGINE = 'zlib'
    DEFAULT_LEVEL = 9

    def __init__(self, *args, **kwargs):

        # compression engine to use
        engine = kwargs.pop('engine', None)
        if engine is None:
            engine = self.DEFAULT_ENGINE
            if engine is None:
                engine = 'dummy'
        if engine not in self.engines:
            raise ValueError(text.format('Unknown compression engine (%s), must be one of %s', engine,
                                         ', '.join(repr(key) for key in sorted(self.engines))))
        self.engine = self.engines[engine]

        # compression level to use (if applicable)
        level = kwargs.pop('level', None)
        if level is None:
            level = self.DEFAULT_LEVEL
        if not isinstance(level, (int, long)):
            raise TypeError(text.format('compression_level must be an int, not %r', type(level).__name__))
        if ((level < 1) or (level > 9)):
            raise ValueError(text.format('compression_level must be between 1-9, not %d', level))
        self.level = level

        # continue field construction
        super(SerializedDataField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        """Convert serialized data into python object"""
        if value is not None:
            if not isinstance(value, str):
                value = text.encode(value, settings.TEXT_ENCODING)
            offset = len(self.HEADER)
            if (len(value) > (offset + 6)) and value.startswith(self.HEADER):
                id = value[offset]
                engine = self.engine_ids.get(id)
                if engine is not None:
                    encoded_data = buffer(value, offset + 1)
                    compressed_data = base64.decodestring(encoded_data)
                    value = engine.decompress(compressed_data, self.level)
            return value

    def get_db_prep_value(self, value):
        """Serialize data before storing to database"""
        if value is not None:
            if not isinstance(value, str):
                value = text.encode(value, settings.TEXT_ENCODING)
            compressed_data = self.engine.compress(value, self.level)
            encoded_data = base64.encodestring(compressed_data)
            parts = self.HEADER, self.engine.id, encoded_data
            joined = ''.join(parts)
            value = text.decode(joined, settings.TEXT_ENCODING)
            return value

    def value_to_string(self, obj):
        """Convert value to string"""
        return self.get_db_prep_value(self._get_val_from_obj(obj))

    def get_internal_type(self):
        """Underlying django Field to use"""
        return 'TextField'

    def zlib_compress(data, level=None):
        """Compress data using zlib"""
        return zlib.compress(data, level)

    def zlib_decompress(data, level=None):
        """Decompresses zlib-compressed data"""
        return zlib.decompress(data)

    def gzip_compress(data, level=None):
        """Compress data using gzip"""
        fileobj = stringio.StringIO()
        fp = gzip.GzipFile(fileobj=fileobj, mode='w', compresslevel=level)
        fp.write(data)
        return fileobj.getvalue()

    def gzip_decompress(data, level=None):
        """Decompresses gzip-compressed data"""
        fileobj = stringio.StringIO(data)
        fp = gzip.GzipFile(fileobj=fileobj, mode='r')
        return fp.read()

    def dummy(data, level=None):
        """Fake (de)compression for debug purposes"""
        return data

    Engine = collections.namedtuple('Engine', 'id compress decompress')

    engines = {'zlib': Engine('z', zlib_compress, zlib_decompress),
               'gzip': Engine('g', gzip_compress, gzip_decompress),
               'dummy': Engine('d', dummy, dummy)}

    engine_ids = dict((engine.id, engine) for engine in engines.itervalues())
