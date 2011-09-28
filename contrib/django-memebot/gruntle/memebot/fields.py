"""Custom model fields"""

import collections
import base64
import zlib
import gzip
import sys

try:
    import cStringIO as stringio
except ImportError:
    import StringIO as stringio

try:
    import cPickle as pickle
except ImportError:
    import pickle

from django.db import models
from django.conf import settings
from gruntle.memebot.utils import text

__all__ = ['SerializedDataField', 'PickleField', 'AttributeDataWrapper',
           'AttributeManager', 'KeyValueDataWrapper', 'KeyValueManager']

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


class PickleField(models.Field):

    """Field that can store arbitrary python objects, pickling on the backend"""

    __metaclass__ = models.SubfieldBase

    DEFAULT_HEADER = 'PickleField:'
    DEFAULT_ENCODING = 'utf-8'

    def __init__(self, *args, **kwargs):
        header = kwargs.pop('header', None)
        encoding = kwargs.pop('encoding', None)
        if header is None:
            header = self.DEFAULT_HEADER
        if encoding is None:
            encoding = self.DEFAULT_ENCODING
        self.header = header
        self.encoding = encoding
        super(PickleField, self).__init__(*args, **kwargs)

    @property
    def header_offset(self):
        """Byte offset to end of header"""
        return len(self.header)

    def to_python(self, value):
        """Convert serialized data into python object"""
        if isinstance(value, (str, unicode)) and value.startswith(self.header):
            if isinstance(value, unicode):
                value = text.encode(value, self.encoding)
            value = pickle.loads(value[self.header_offset:])
        return value

    def get_db_prep_value(self, value):
        """Serialize data before storing to database"""
        if value is not None:
            value = pickle.dumps(value)
            value = text.decode(value, self.encoding)
            value = self.header + value
        return value

    def value_to_string(self, obj):
        """Convert value to string"""
        return self.get_db_prep_value(self._get_val_from_obj(obj))

    def get_internal_type(self):
        """Underlying django Field to use"""
        return 'TextField'


class AttributeDataWrapper(object):

    """Wraps access to a single object's attribute storage"""

    __slots__ = '_object', '_field', '_default', '_writeback', '_dirty', '_data'

    def __init__(self, object, field, default, writeback):
        self._object = object
        self._field = field
        self._default = default
        self._writeback = writeback
        self._dirty = False
        self._data = getattr(object, field, None)
        if self._data is None:
            self._data = {}
        elif not isinstance(self._data, dict):
            raise TypeError('storage must be a dictionary, not %r' % type(self._data).__name__)

    def _save(self):
        """Write changes to underlying dictionary back to storage field"""
        setattr(self._object, self._field, self._data)
        result = self._object.save()
        self._dirty = False
        return result

    def __getattribute__(self, key):
        """If not an attribute of this manager, try to find it in the storage dict"""
        try:
            return super(AttributeDataWrapper, self).__getattribute__(key)
        except AttributeError:
            return self._data.get(key, self._default)

    def __setattr__(self, key, val):
        """Write to attribute storage: First check if it's a manager attribute, then pass on to storage"""
        if key in type(self).__slots__:
            super(AttributeDataWrapper, self).__setattr__(key, val)
        else:
            self._data[key] = val
            if self._writeback:
                self._save()
            else:
                self._dirty = True

    # map index to attribute access for convenience
    __getitem__ = __getattribute__
    __setitem__ = __setattr__


class AttributeManager(object):

    """
    Descriptor interface combined with PickleField for data storage allows for
    transparent read/write access of an arbitrary number of attributes. They may
    be of any pickle-able python object
    """

    DEFAULT_STORAGE_FIELD = 'attr_storage'
    DEFAULT_DEFAULT_VALUE = None
    DEFAULT_WRITEBACK = True

    def __init__(self, storage_field=None, default_value=None, writeback=None):
        if storage_field is None:
            storage_field = self.DEFAULT_STORAGE_FIELD
        if default_value is None:
            default_value = self.DEFAULT_DEFAULT_VALUE
        if writeback is None:
            writeback = self.DEFAULT_WRITEBACK
        self.storage_field = storage_field
        self.default_value = default_value
        self.writeback = writeback

    def __get__(self, object, model):
        """Descriptor access: return wrapper around the object to manage its data store"""
        return AttributeDataWrapper(object, self.storage_field, self.default_value, self.writeback)


class KeyValueDataWrapper(object):

    """Wraps a model and manages its key/value pairing with explicit writeback"""

    __slots__ = '_model', '_key', '_val', '_default', '_writeback', '_dirty'

    def __init__(self, model, key, val, default, writeback):
        self._model = model
        self._key = key
        self._val = val
        self._default = default
        self._writeback = writeback
        self._dirty = set()

    def _save(self):
        dirty, self._dirty = self._dirty, set()
        for object in dirty:
            object.save()

    def __getattribute__(self, key):
        try:
            return super(KeyValueDataWrapper, self).__getattribute__(key)
        except AttributeError:
            try:
                return getattr(self._model.objects.get(**{self._key: key}), self._val, self._default)
            except self._model.DoesNotExist:
                return self._default

    def __setattr__(self, key, val):
        if key in type(self).__slots__:
            super(KeyValueDataWrapper, self).__setattr__(key, val)
        else:
            object = self._model.objects.get_or_create(**{self._key: key})[0]
            setattr(object, self._val, val)
            if self._writeback:
                object.save()
            else:
                self._dirty.add(object)

    __getitem__ = __getattribute__
    __setitem__ = __setattr__


class KeyValueManager(object):

    """Descriptor access: Return model wrapper to manage model's key/value pairing"""

    DEFAULT_KEY_FIELD = 'name'
    DEFAULT_VAL_FIELD = 'value'
    DEFAULT_DEFAULT_VALUE = None
    DEFAULT_WRITEBACK = True

    def __init__(self, key_field=None, val_field=None, default_value=None, writeback=None):
        if key_field is None:
            key_field = self.DEFAULT_KEY_FIELD
        if val_field is None:
            val_field = self.DEFAULT_VAL_FIELD
        if default_value is None:
            default_value = self.DEFAULT_DEFAULT_VALUE
        if writeback is None:
            writeback = self.DEFAULT_WRITEBACK
        self.key_field = key_field
        self.val_field = val_field
        self.default_value = default_value
        self.writeback = writeback

    def __get__(self, object, model):
        return KeyValueDataWrapper(model, self.key_field, self.val_field, self.default_value, self.writeback)
