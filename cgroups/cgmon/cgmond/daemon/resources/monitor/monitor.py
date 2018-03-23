
from cgmond.daemon.resources.interfaces import Resource
from cgmond.daemon.cgroup import MonitorCgroup


class MonitorMonitorCgroup(MonitorCgroup):
    hierarchy = 'monitor'

    def __init__(self, monitor_name):
        super(MonitorMonitorCgroup, self).__init__(self.hierarchy, monitor_name)

    def set_limits(self, app, limit):
        pass

    def get_limits(self, app):
        return None


class MonitorResource(Resource):
    name = 'Monitor'
    hierarchy = 'monitor'
    policy = None
    default_policy = None
    default_usage = None
    default_limit = 'external'

    def __init__(self, monitor, policy=None, usage=None, limit=None):
        super(MonitorResource, self).__init__(monitor, policy, usage, limit)
        # monitor_cg = MonitorMonitorCgroup(self.monitor.name)
        # monitor_cg._ensure_base_paths()

    def create(self, name):
        """ Initialize name """
        self.limit.create(name)

    def add(self, name, pid):
        """ Add a given pid in the monitor's hierarchy cgroup """
        self.limit.add(name, pid)

    def set_limit(self, name, limit):
        pass

#   def add_app(self, app):
#       pass

    def set_limits(self, apps, limits):
        pass

    def get_usage(self, apps):
        pass

    def remove_app(self, app):
        self.limit.delete(app)

    def get_resource_usage(self):
        return None

    def list_apps(self):
        monitor_cg = MonitorMonitorCgroup(self.monitor.name)
        return monitor_cg.list()
