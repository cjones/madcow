"""Utilities for working with dates and times"""

import datetime
import decimal
import rfc822
import time
import os

class TZContext(object):

    def __init__(self, tz=None):
        self.tz = tz
        self.orig = os.environ.get('TZ')
        self.level = 0

    def __enter__(self):
        self.level += 1
        if self.level == 1:
            self.tzset(self.tz)
        return self

    def __exit__(self, *exc_info):
        if self.level > 0:
            self.level -= 1
            if self.level == 0:
                self.tzset(self.orig)
        return False

    @staticmethod
    def tzset(tz=None):
        if tz is None:
            try:
                del os.environ['TZ']
            except KeyError:
                pass
        else:
            os.environ['TZ'] = tz
        time.tzset()


class TZInfo(datetime.tzinfo):

    def __init__(self, tz=None):
        super(TZInfo, self).__init__()
        self.context = TZContext(tz)
        with self.context:
            self.names = tuple(time.tzname)
            std_offset = datetime.timedelta(seconds=-time.timezone)
            dst_offset = datetime.timedelta(seconds=-time.altzone) if time.daylight else std_offset
            self.offsets = std_offset, dst_offset
            self.diffs = datetime.timedelta(0), dst_offset - std_offset

    @property
    def name(self):
        return self.names[0]

    def utcoffset(self, dt):
        return self.offsets[self.is_dst(dt)]

    def dst(self, dt):
        return self.diffs[self.is_dst(dt.replace(tzinfo=None))]

    def tzname(self, dt):
        return self.names[self.is_dst(dt)]

    def is_dst(self, dt):
        with self.context:
            return time.localtime(time.mktime(dt.timetuple())).tm_isdst > 0

    def __reduce__(self):
        return self.__class__, (self.context.tz,)

    def __hash__(self):
        return hash(self.names)

    def __eq__(self, other):
        if isinstance(other, TZInfo):
            return hash(self) == hash(other)
        return NotImplemented

    def __ne__(self, other):
        eq = self.__eq__(other)
        if eq is NotImplemented:
            return eq
        return not eq

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.name)


class tzdatetime(datetime.datetime):

    def __new__(cls, *args, **kwargs):
        dt = super(tzdatetime, cls).__new__(cls, *args, **kwargs)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=local)
        return dt.replace(microsecond=0)

    @property
    def unixtime(self):
        dt = self.astimezone(local)
        tt = dt.timetuple()
        return int(time.mktime(tt))

    def rfc822format(self):
        return rfc822.formatdate(self.unixtime)

    def isoformat(self, *args, **kwargs):
        return super(tzdatetime, self).isoformat(*args, **kwargs).replace('+00:00', 'Z')

    def astimezone(self, *args, **kwargs):
        return tzdatetime.fromdatetime(super(tzdatetime, self).astimezone(*args, **kwargs))

    def as_utc(self):
        if self.tzinfo is utc:
            return self
        return self.astimezone(utc)

    utc = property(as_utc)

    @classmethod
    def fromdatetime(cls, dt):
        return cls(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, 0, dt.tzinfo)

    @classmethod
    def new(cls, t=None):
        """Convert different time values to a tzdate"""
        orig_type = type(t)
        if t is None:
            t = datetime.datetime.now()
        elif orig_type is datetime.date:
            t = datetime.datetime.fromordinal(t.toordinal())
        elif not isinstance(t, datetime.datetime):
            if isinstance(t, time.struct_time):
                t = time.mktime(t)
            if isinstance(t, (float, decimal.Decimal)):
                t = int(round(t, 0))
            if not isinstance(t, (int, long)):
                raise TypeError('unknown time format: ' + orig_type.__name__)
            t = datetime.datetime.fromtimestamp(t)
        if t.tzinfo is None:
            t = t.replace(tzinfo=local)
        return cls.fromdatetime(t)


local = TZInfo()
utc = TZInfo('UTC')
