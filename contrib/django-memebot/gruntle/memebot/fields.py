
import base64
from django.db import models

class BinaryField(models.Field):

    __metaclass__ = models.SubfieldBase

    MAGIC = 'binary:'

    def to_python(self, val):
        if isinstance(val, (str, unicode)) and val.startswith(self.MAGIC):
            if isinstance(val, unicode):
                val = val.encode('ascii')
            val = buffer(val, len(self.MAGIC))
            i = val.index(':')
            encoded_content = buffer(val, i)
            val = val[:i], base64.decodestring(encoded_content)
        return val

    def get_db_prep_value(self, val):
        if val is not None:
            content_type, content = val
            return u':'.join((self.MAGIC, content_type, base64.encodestring(content)))

    def value_to_string(self, object):
        return self.get_db_prep_value(self._get_val_from_obj(object))

    def get_internal_type(self):
        return 'TextField'
