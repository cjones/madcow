
import functools
import traceback
import sys
from gruntle.memebot.utils import get_logger, text

def logged(*args, **kwargs):
    logger = get_logger(*args, **kwargs)

    def decorator(wrapped_func):

        @functools.wraps(wrapped_func)
        def wrapper_func(*args, **kwargs):
            try:
                return wrapped_func(*((logger,) + args), **kwargs)
            except (SystemExit, KeyboardInterrupt, EOFError):
                raise
            except:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                logger.error('Unhandled exception in %s', wrapped_func.func_name)
                for line in traceback.format_exception(exc_type, exc_value, exc_traceback):
                    logger.error(text.chomp(line))
                raise exc_type, exc_value, exc_traceback

        return wrapper_func
    return decorator
