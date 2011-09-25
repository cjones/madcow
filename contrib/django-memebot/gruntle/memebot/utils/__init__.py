"""Generic shared utility methods"""

import logging
import sys

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


def get_logger(name, level=None, stream=None, append=False):
    pass


# default trapper that swallows errors
trapped = TrapErrors(reraise=False)
