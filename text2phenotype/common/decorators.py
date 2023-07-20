import sys
import time

from typing import Tuple
from functools import wraps

from text2phenotype.common.log import operations_logger


def retry(ExceptionsToCheck: Tuple[Exception], tries: int = 6, logger: 'Logger' = None, backoff_factor: float = 0.1):
    """Retry calling the decorated function.

    http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry

    backoff_factor == 0     -> retry immediately, no timeout
    backoff_factor == 0.1   -> timeouts: 0.1, 0.2, 0.4, 0.8, 1.6, 3.2, 6.4, ...
    backoff_factor == 0.5   -> timeouts: 0.5, 1, 2, 4, 8, 16, ...
    backoff_factor == 1     -> timeouts: 1, 2, 4, 8, 16, ...
    """
    backoff_factor = backoff_factor or 0

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            attempt = 1

            while attempt < tries:
                try:
                    return f(*args, **kwargs)
                except ExceptionsToCheck as err:
                    timeout = backoff_factor * 2 ** (attempt - 1)  # Exponential backoff

                    msg = (f"Attempt {attempt}: {str(err)}, retrying in "
                           f"{timeout:0.1f} seconds...")

                    if logger:
                        logger.warning(msg)
                    else:
                        operations_logger.warning(msg)

                    time.sleep(timeout)
                    attempt += 1
            else:
                return f(*args, **kwargs)

        return wrapper
    return decorator
