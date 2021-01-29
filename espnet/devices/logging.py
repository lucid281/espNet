import functools
import time
import datetime


def log_execution_time(func):
    @functools.wraps(func)
    def wrapper_timer(*args, **kwargs):
        tic = time.perf_counter()
        value = func(*args, **kwargs)
        toc = time.perf_counter()
        elapsed_time = toc - tic
        print(f"[{datetime.datetime.now().isoformat()}] {func.__dict__} {func.__name__} in {elapsed_time:<.3f}s with {args}")
        return value

    return wrapper_timer
