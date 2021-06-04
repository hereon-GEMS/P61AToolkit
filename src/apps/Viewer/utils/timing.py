import time


def log_ex_time(fn):
    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        result = fn(*args, **kwargs)
        t1 = time.perf_counter()
        if hasattr(args[0], 'logger'):
            args[0].logger.debug('%s: executed in %.01f ms' % (fn.__name__, (t1 - t0) * 1e3))
        else:
            print('%s: executed in %.01f ms' % (fn.__name__, (t1 - t0) * 1e3))
        return result
    return wrapper
