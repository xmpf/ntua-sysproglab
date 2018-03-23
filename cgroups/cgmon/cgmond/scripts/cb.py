#!/usr/bin/python

import sys
import jsonrpclib


def remove(name):
    """ Notify cgmon server """

    jsonrpclib.config.version = 1.0
    server = jsonrpclib.Server('http://localhost:8080')
    server.remove(name)


def extract_values(cgroup_path):
    """ Extract monitor name and task name from cgroups path """

    monitor_name, task_name = cgroup_path.lstrip('/').split('/')
    return monitor_name, task_name


def main():
    # if len(sys.arv) != 2:
    #     syslog missing arguments
    cb_arg = sys.argv[1]
    _, task_name = extract_values(cb_arg)
    remove(task_name)


if __name__ == '__main__':
    main()
