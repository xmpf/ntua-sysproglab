import os
from cgmond.utils import ensure_path

# TODO maybe move this to a configuration option
CGROUP_BASE_PATH = '/sys/fs/cgroup'

class Cgroup(object):
    """
    Basic cgroup interface to interact with the cgroup filesystem.
    """
    hierarchy = None
    # TODO Decide whether to use  cgroups.procs or not?
    pid_file = 'tasks'

    def __init__(self, hierarchy, path):
        self.hierarchy = hierarchy
        self.path = path

    @staticmethod
    def get_base_path(hierarchy):
        """ Return the system path of the hierarchy """
        return os.path.join(CGROUP_BASE_PATH, hierarchy)

    def get_path(self):
        """ Return the path of the specified cgroup """
        return os.path.join(Cgroup.get_base_path(self.hierarchy), self.path)

    def get_pidfile_path(self):
        """ Return the path of the PID file. """
        return os.path.join(self.get_path(), self.pid_file)


    def add(self, pid):
        """ Add the PID to the specified cgroup """
        # TODO kill first ?
        with open(self.get_pidfile_path(), 'a+') as f:
            f.write("%s\n" % str(pid))

#   def remove(self, pid):
#       # TODO maybe on CGROUP_BASE_PATH, hierarchy, base_path ?
#       #      to ensure permissions ?
#       path = os.path.join(CGROUP_BASE_PATH, hierarchy, self.pid_file)
#       with open(path, 'a+') as f:
#           f.write("%s\n" % str(pid))

    def list(self):
        """ List the PIDs of the specified cgroup """
        with open(self.get_pidfile_path(), 'r') as f:
            cgroup_pids = [pid for pid in f.read().rstrip('\n').split('\n') if pid != '']
            return cgroup_pids

    def delete(self):
        """ Delete the cgroup directory """
        path = self.get_path()
        os.rmdir(path)


class MonitorCgroup(object):
    """
    A cgroup abstraction as it used by the monitor.

    This class offers an abstraction layer to use cgroups with cgmon.
    """
    monitor_name = None
    hierarchy = None

    def __init__(self, hierarchy, monitor_name):
        self.hierarchy = hierarchy
        self.monitor_name = monitor_name


    def _get_base_path(self):
        return os.path.join(Cgroup.get_base_path(self.hierarchy), self.monitor_name)


    def _get_task_path(self, name):
        return os.path.join(self._get_base_path(), name)


    def _ensure_base_paths(self):
        """ Ensure all paths present up to the monitor cgroup """
        # TODO maybe ignore paths before CGROUP_BASE_PATH.
        # TODO maybe ensure proper permissions

        ensure_path(self._get_base_path())


    def _ensure_task_path(self, name):
        """ Ensure all paths present up to the task cgroup """
        ensure_path(self._get_task_path(name))


    def create(self, name):
        """ Create a new task cgroup """
        self._ensure_task_path(name)


    def add(self, name, pid):
        """ Add a new process to the given task/application """
        # self._ensure_task_path(name)
        # self.ensure_default_values()
        cg = Cgroup(self.hierarchy, os.path.join(self.monitor_name, name))
        cg.add(pid)


    def list(self, empty=False):
        """
        List all (non-empty) task cgroup directories

        This returns the task found on the specified hierarchy for the given
        monitor.
        """
        dirs = [d for d in os.listdir(self._get_base_path())
                if os.path.isdir(os.path.join(self._get_base_path(), d))]
        if not empty:
            dirs = [d for d in dirs
                    if len(Cgroup(self.hierarchy, self._get_task_path(d)).list()) > 0]

        return dirs


    def delete(self, name):
        """
        Remove task from the cgroup

        This succeeds only if no processes remain in the given task.
        """
        cg = Cgroup(self.hierarchy, os.path.join(self.monitor_name, name))
        cg.delete()


    def set_limit(self, name, limit_name, value):
        """ Sets the limit exposed by the limit file to the specified value """
        path = os.path.join(self._get_task_path(name), limit_name)
        with open(path, 'w') as f:
                f.write("%s\n" % str(value))


    def get_limit(self, name, limit_name):
        """ Return the limit value exposed by the limit file """
        path = os.path.join(self._get_task_path(name), limit_name)
        with open(path, 'r') as f:
                return f.read().rstrip('\n')


#   def remove_task(self, task):
#       cg = Cgroup(self.hierarchy, '')
#       cg.add(task.pid)

#    def ensure_default_values(self):
#        # TODO raise NotImplemented()
#        pass
