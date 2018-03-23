
from itertools import islice
from cgmond.daemon.resources.interfaces import Usage
from cgmond.daemon.resources.interfaces import ResourceCgroup


class CPUUsage(object):
    def __init__(self, user, system):
        self.user = user
        self.system = system

    def __add__(self, other):
        u = self.user + other.user
        s = self.system + other.system
        return CPUUsage(u, s)

    def __sub__(self, other):
        u = self.user - other.user
        s = self.system - other.system
        return CPUUsage(u, s)

    @property
    def total(self):
        return self.user + self.system

    def __str__(self):
        return "CPUUsage(User=%d, System=%d, Total=%d)" % (self.user, self.system, self.total)

    def __repr__(self):
        return str(self)


class CPUUsageCgroup(ResourceCgroup):


    def __init__(self, monitor_name):
        super(CPUUsageCgroup, self).__init__('cpuacct', monitor_name)


    def get_usage(self, name):
        raw_value = self.get_limit(name, 'cpuacct.stat')
        values = [line.split()[1] for line in raw_value.split('\n')]

        return CPUUsage(int(values[0]), int(values[1]))


class CUsage(Usage):

    prev_overall_usage = None
    prev_resource_usage = None
    prev_usage = None

    def __init__(self, monitor_name, **kwargs):
        super(CUsage, self).__init__(monitor_name, **kwargs)
        self.prev_usage = {}


    def get_usage(self, tasks):
        # first gather usage for all tasks
        # then gather resource usage
        # then gather overall usage
        # this way, we can be closer to goal cpu usage per task <= resource usage <= overall usage
        # since cpu stats are monotonically increased

        current = {}
        cpu_cg = CPUUsageCgroup(self.monitor_name)
        for tname in tasks:
            t = tasks[tname]
            task_usage = cpu_cg.get_usage(t.name)
            self.logger.debug("Got task usage %s for task %s" % (task_usage, tname))
            current[tname] = task_usage

        # TODO use separate prev_resource_usage for this function
        resource_usage = self.get_resource_usage()
        total_cpu = self.get_total_available()


        usage = {}
        prev_usage = {}

        for tname in tasks:
            t = tasks[tname]
            c_usage = current[tname]
            p_usage = self.prev_usage.get(t.name, None)
            if self.prev_overall_usage is not None and p_usage is not None:
                usage[t.name] = {}
                usage[t.name]['total_available']  = total_cpu - self.prev_overall_usage
                usage[t.name]['resource_usage']  = resource_usage
                usage[t.name]['usage'] =  c_usage - p_usage
                self.logger.debug("Calculated usage %s for task %s" % (usage[t.name], tname))
            prev_usage[t.name] = c_usage

        self.prev_usage = prev_usage
        self.prev_overall_usage = total_cpu

        return usage


    def get_resource_usage(self):
        cpu_cg = CPUUsageCgroup(self.monitor_name)
        resource_usage = cpu_cg.get_usage('')
        if self.prev_resource_usage is not None:
            usage = resource_usage - self.prev_resource_usage
        else:
            usage = CPUUsage(0, 0)

        self.prev_resource_usage = resource_usage

        return usage

    def get_total_available(self):
        """ Return total CPU usage (including idle) as reported by /proc/stat"""

        stat_path = '/proc/stat'
        with open(stat_path) as f:
            cpu_line = next(f)

        return sum(int(time) for time in islice(cpu_line.split(), 1, None))


    def create(self, task):
        cpu_cg = CPUUsageCgroup(self.monitor_name)
        cpu_cg.create(task)


    def add(self, task, pid):
        cpu_cg = CPUUsageCgroup(self.monitor_name)
        cpu_cg.add(task, pid)


    def delete(self, task):
        cpu_cg = CPUUsageCgroup(self.monitor_name)
        cpu_cg.delete(task)
        if self.prev_usage.get(task, None) is not None:
            del self.prev_usage[task]
