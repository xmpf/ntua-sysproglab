import os
import errno
import inspect
import imp
import subprocess
from itertools import izip
from .exceptions import ExternalInvocationException

def ensure_path(path, permissions=None, user=None, group=None):
    # mkdir path
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno == errno.EEXIST:
            # CHECK if dir, etc
            return
    # fix permissions ?


def load_subclasses(namespace, cls):
    policies = {}

    for entry in os.listdir(namespace):
        filename = os.path.basename(entry)
        name, file_ext =  os.path.splitext(filename)
        if filename == '__init__.py' or file_ext != ".py":
            continue

        m = imp.load_source(name, os.path.join(namespace, filename))
        for attr, value in inspect.getmembers(m, inspect.isclass):
            if value.__name__ in [cls.__name__]:
                continue

            if not issubclass(value, cls):
                continue

            policies[name] = value

    return policies


def check_output(exe, args, inp=None):
    """
    Call a subprocess with a given set of arguments and input.

    Similar to Popen's check_output but takes an optional input to be passed to
    process's standard input.
    """

    cmd = [exe] + args
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    output, error = p.communicate(input=inp)

    exit_code = p.wait()

    if exit_code != 0:
        raise ExternalInvocationException(exit_code, error)

    return output, error

def grouped(iterable, n):
    return izip(*[iter(iterable)]*n)
