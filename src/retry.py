import time
import functools
from src.exceptions import TransientServiceError, PermanentServiceError

def retry_on_transient(initial_delay=5.0, backoff_factor=2.0, max_attempts=3):
    """
    Decorator that retries a function when it raises TransientServiceError.
    It does NOT retry on PermanentServiceError (or its subclasses).
    """
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            attempt = 0
            delay = initial_delay
            while True:
                try:
                    return fn(*args, **kwargs)
                except PermanentServiceError:
                    #  never retry on permanent errors
                    raise
                except TransientServiceError:
                    attempt += 1
                    if attempt > max_attempts:
                        raise
                    print(f"[retry] attempt {attempt} failed; sleeping {delay}s before retry")
                    time.sleep(delay)
                    delay *= backoff_factor
        return wrapper
    return decorator