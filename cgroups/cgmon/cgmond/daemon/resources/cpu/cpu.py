
from cgmond.daemon.resources.interfaces import Resource

class CPUResource(Resource):
    name = 'CPU'
    hierarchy = 'cpu'
    policy = None
    usage = None
    limit = None
    default_policy = 'cpulimit'
    default_usage = 'usage'
    default_limit = 'limit'

    def __init__(self, monitor, policy=None, usage=None, limit=None):
        super(CPUResource, self).__init__(monitor, policy, usage, limit)


    def create(self, name):
        """ Initialize  """
        self.logger.debug("Creating CPU resource for %s" % name)
        self.limit.create(name)
        self.logger.info("Created CPU cgroup for %s" % name)

    def add(self, name, pid):
        """ Add a given pid in the CPU cgroup of the app """
        self.logger.debug("Adding %d in CPU cgroup for %s" % (pid, name))
        self.limit.add(name, pid)
        self.logger.info("Added %d in CPU cgroup for %s" % (pid, name))

    def set_limit(self, name, limit):
        """ Set a CPU limit to a cgroup's app """
        self.logger.debug("Setting limit for %s to %s" % (name, limit))
        self.limit.set_limit(name, limit.shares)
        self.logger.info("Set limit for %s to %s" % (name, limit))


    def set_limits(self, apps, limits):
        return self.limit.set_limits(apps, limits)


    def get_limits(self, apps):
        return self.limit.get_limits(apps)


    def get_usage(self, apps):
        return self.usage.get_usage(apps)


    def get_resource_usage(self):
        return self.usage.get_resource_usage()


    def remove_app(self, app):
        self.logger.debug("Removing app %s" % app)
        self.limit.delete(app)
        self.logger.info("Removed app %s" % app)
