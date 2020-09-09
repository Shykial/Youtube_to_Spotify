import time


def timer(function):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = function(*args, **kwargs)
        print(f'Function {function.__name__} execution took: {time.time() - start_time}')
        return result
    return wrapper
