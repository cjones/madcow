"""Decorator magic.. abstract some ugly, repetitive stuff out"""

import functools
import traceback
import sys

from django.core.cache import cache

from gruntle.memebot.utils import get_logger, text, locking, make_unique_key
from gruntle.memebot.exceptions import *

class NoResult(object):

    """Represents function that returned None rather than empty cache item"""


def logged(*logger_args, **default_logger_kwargs):

    """
    This decorator creates a logger when called, injecting it as the first
    argument, and logging any unhandled exceptions. You may add a console
    stream on the fly with log_stream kwargument to the wrapped function.
    """

    method = default_logger_kwargs.pop('method', False)

    def decorator(wrapped_func):

        @functools.wraps(wrapped_func)
        def wrapper_func(*args, **kwargs):
            logger = kwargs.pop('logger', None)
            if logger is None:
                logger_kwargs = dict(default_logger_kwargs)
                logger_kwargs.setdefault('stream', kwargs.pop('log_stream', None))
                logger = get_logger(*logger_args, **logger_kwargs)

            try:
                with TrapErrors():
                    if method:
                        args[0].log = logger
                    else:
                        args = (logger,) + args
                    return wrapped_func(*args, **kwargs)

            except TrapError, exc:
                logger.error('Unhandled exception in %s', wrapped_func.func_name)
                for line in traceback.format_exception(*exc.args):
                    logger.error(text.chomp(line))
                reraise(*exc.args)

        return wrapper_func
    return decorator


def locked(*lock_args, **lock_kwargs):

    """This decorator wraps a functino call with attempt to acquire lock for the duration"""

    def decorator(wrapped_func):

        @functools.wraps(wrapped_func)
        def wrapper_func(*args, **kwargs):
            with locking.Lock(*lock_args, **lock_kwargs):
                return wrapped_func(*args, **kwargs)

        return wrapper_func
    return decorator


def memoize(*args, **kwargs):

    """This decorator wraps a function and caches results based on arguments passed in"""

    _key_fmt = kwargs.pop('key_fmt', None)
    cache_none = kwargs.pop('cache_none', True)

    def decorator(wrapped_func):
        if _key_fmt is None:
            key_fmt = 'memoize:%s:%%d' % wrapped_func.func_name
        else:
            key_fmt = _key_fmt

        @functools.wraps(wrapped_func)
        def wrapper_func(*args, **kwargs):
            key = key_fmt % make_unique_key((args, kwargs))
            val = cache.get(key)
            if val is None:
                val = wrapped_func(*args, **kwargs)
                if cache_none and val is None:
                    val = NoResult
                cache.set(key, val)
            if cache_none and val is NoResult:
                val = None
            return val

        return wrapper_func

    if len(args) == 1 and not kwargs and callable(args[0]):
        return decorator(args[0])
    return decorator


def login_or_apikey_required(*args, **kwargs):

    """TBD: Like login required, but allow API access as well"""

    def decorator(wrapped_func):

        @functools.wraps(wrapped_func)
        def wrapper_func(request, *args, **kwargs):
            return wrapped_func(request, *args, **kwargs)

        return wrapper_func

    if len(args) == 1 and not kwargs and callable(args[0]):
        return decorator(args[0])
    return decorator
