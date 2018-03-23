
from collections import namedtuple
from cgmond.daemon.resources.interfaces import Limit
from cgmond.daemon.resources.interfaces import ResourceCgroup


CPULimit = namedtuple('CPULimit', ['shares'])

class CPUCgroup(ResourceCgroup):

    def __init__(self, monitor_name):
        super(CPUCgroup, self).__init__('cpu', monitor_name)


    def set_shares(self, name, shares):
        self.set_limit(name, 'cpu.shares', shares)


    def get_shares(self, name):
        return self.get_limit(name, 'cpu.shares')


class CLimit(Limit):
    hierarchy = 'cpu'

    def __init__(self, monitor_name, **kwargs):
        super(CLimit, self).__init__(monitor_name, **kwargs)


    def create(self, name):
        """ Initialize CPU cgroup for task """
        self.logger.debug("Creating CPU cgroup for %s" % name)
        cpu_cg = CPUCgroup(self.monitor_name)
        cpu_cg.create(name)
        self.logger.info("Created CPU cgroup for %s" % name)

    def add(self, name, pid):
        """ Add a given pid in the CPU cgroup of the task """
        self.logger.debug("Adding %d in CPU cgroup for %s" % (pid, name))
        cpu_cg = CPUCgroup(self.monitor_name)
        cpu_cg.add(name, pid)
        self.logger.info("Added %d in CPU cgroup for %s" % (pid, name))

    def set_limit(self, name, limit):
        """ Set a CPU limit to a cgroup's task """
        self.logger.debug("Setting limit for %s to %s" % (name, limit))
        cpu_cg = CPUCgroup(self.monitor_name)
        cpu_cg.set_shares(name, limit.shares)
        self.logger.info("Set limit for %s to %s" % (name, limit))


    def set_limits(self, tasks, limits):
        for tname in tasks:
            t = tasks[tname]
            if limits.get(t.name, None) is not None:
                self.set_limit(t.name, limits[t.name])
            else:
                self.logger.debug("Skipping setting limit for %s" % t.name)
            #   cpu_cg = CPUMonitorCgroup(self.monitor_name)
            #   cpu_cg.remove_task(t)

    def get_limits(self, tasks):
        cpu_cg = CPUCgroup(self.monitor_name)

        limits = {}
        for tname in tasks:
            t = tasks[tname]
            limits[t.name] = CPULimit(cpu_cg.get_shares(t.name))

        return limits


    def delete(self, task):
        self.logger.debug("Removing task %s" % task)
        cpu_cg = CPUCgroup(self.monitor_name)
        cpu_cg.delete(task)
        self.logger.info("Removed task %s" % task)
