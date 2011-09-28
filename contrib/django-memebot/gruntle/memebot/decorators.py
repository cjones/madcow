"""Decorator magic.. abstract some ugly, repetitive stuff out"""

import functools
import traceback
import sys

from gruntle.memebot.utils import get_logger, text, locking
from gruntle.memebot.exceptions import *

def logged(*logger_args, **default_logger_kwargs):

    """
    This decorator creates a logger when called, injecting it as the first
    argument, and logging any unhandled exceptions. You may add a console
    stream on the fly with log_stream kwargument to the wrapped function.
    """

    def decorator(wrapped_func):

        @functools.wraps(wrapped_func)
        def wrapper_func(*args, **kwargs):
            try:
                with TrapErrors():
                    # hijack log_stream kwarg and use that to update our defaults
                    logger_kwargs = dict(default_logger_kwargs)
                    logger_kwargs.setdefault('stream', kwargs.pop('log_stream', None))

                    # inject logger into first argument
                    logger = get_logger(*logger_args, **logger_kwargs)
                    new_args = [logger]
                    new_args.extend(args)
                    args = tuple(new_args)

                    # call decorated function
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
