"""Decorator magic"""

import functools
import traceback
import sys

from gruntle.memebot.utils import get_logger, text, locking

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
            except (SystemExit, KeyboardInterrupt, EOFError):
                raise
            except:
                # catch non-system exceptions that get raised, log the stack trace, and reraise
                exc_type, exc_value, exc_traceback = sys.exc_info()
                logger.error('Unhandled exception in %s', wrapped_func.func_name)
                for line in traceback.format_exception(exc_type, exc_value, exc_traceback):
                    logger.error(text.chomp(line))
                raise exc_type, exc_value, exc_traceback

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
