
from cgmond.daemon.resources.interfaces import Limit
from cgmond.daemon.resources.interfaces import ResourceCgroup


class MonitorCgroup(ResourceCgroup):

    def __init__(self, monitor_name):
        super(MonitorCgroup, self).__init__('monitor', monitor_name)


class MonitorLimit(Limit):
    hierarchy = 'monitor'

    def __init__(self, monitor_name, **kwargs):
        super(MonitorLimit, self).__init__(monitor_name, **kwargs)


    def create(self, name):
        monitor_cg = MonitorCgroup(self.monitor_name)
        monitor_cg.create(name)

    def add(self, name, pid):
        monitor_cg = MonitorCgroup(self.monitor_name)
        monitor_cg.add(name, pid)

    def delete(self, task):
        monitor_cg = MonitorCgroup(self.monitor_name)
        monitor_cg.delete(task)
