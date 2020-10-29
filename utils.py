import random
from configparser import RawConfigParser
from time import sleep

# load user info from config
parser = RawConfigParser()
parser.read('./project.conf')


def random_wait(min_t=3, max_t=5):
    assert min_t < max_t
    seconds = random.random() * (max_t - min_t) + min_t
    sleep(seconds)


def destructure(dictionary, *keys):
    return [dictionary[k] if k in dictionary else None for k in keys]


def get(dictionary, key):
    keys = key.split(".")
    for k in keys:
        if k not in dictionary:
            return None
        dictionary = dictionary[k]
    return dictionary


def do(func, args=None, kwargs=None, max_retries=3):
    if args is None:
        args = []
    if kwargs is None:
        kwargs = {}

    while max_retries > 0:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Failed to execute {func}, Reason: {e}")
            max_retries -= 1
