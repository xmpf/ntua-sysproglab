
from collections import namedtuple
from cgmond.daemon.resources.interfaces import Limit
from cgmond.utils import check_output


CPULimit = namedtuple('CPULimit', ['shares'])

class ExternalLimit(Limit):
    hierarchy = 'cpu'
    exe = 'cgmon-cgroup-external'
    separator = ':'

    def __init__(self, monitor_name, executable=None, **kwargs):
        super(ExternalLimit, self).__init__(monitor_name, **kwargs)
        if executable is not None:
            self.exe = executable

        self.logger.debug("Using executable '%s'" % self.exe)

    input_prefix = '{sep}{monitor}{sep}{hierarchy}{sep}'
    cmds = {
        'create': 'create' + input_prefix + '{task}\n',
        'add': 'add' + input_prefix + '{task}{sep}{pid}\n',
        'set_limit': 'set_limit' + input_prefix + '{task}{sep}{limit}{sep}{value}\n',
        'get_limit': 'get_limit' + input_prefix + '{task}{sep}{limit}\n',
        'remove': 'remove' + input_prefix + '{task}\n',
    }


    def _format_cmd(self, c, **kwargs):
        return c.format(sep=self.separator, hierarchy=self.hierarchy,
                        monitor=self.monitor_name, **kwargs)

    def __call(self, inp=None):
        self.logger.debug("Calling %s with input %s" % (self.exe, inp.replace('\n', '\\n')))
        return check_output(self.exe, [], inp=inp)

    def _call(self, cmd, **kwargs):
        inp = self._format_cmd(self.cmds[cmd], **kwargs)
        return self.__call(inp=inp)


    def create(self, name):
        """ Initialize CPU cgroup for task """

        self.logger.debug("Creating CPU cgroup for %s" % name)
        self._call('create', task=name)
        self.logger.info("Created CPU cgroup for %s" % name)


    def add(self, name, pid):
        """ Add a given pid in the CPU cgroup of the task """

        self.logger.debug("Adding %d in CPU cgroup for %s" % (pid, name))
        self._call('add', task=name, pid=pid)
        self.logger.info("Added %d in CPU cgroup for %s" % (pid, name))


    def set_limit(self, name, limit):
        """ Set a CPU limit to a cgroup's task """

        self.logger.debug("Setting limit for %s to %s" % (name, limit))
        self._call('add', task=name, limit='cpu.shares', valule=limit.shares)
        self.logger.info("Set limit for %s to %s" % (name, limit))


    def set_limits(self, tasks, limits):
        """ Set a CPU limits to a cgroup tasks """

        inp = ""
        for tname in tasks:
            t = tasks[tname]
            l = limits.get(t.name, None)
            if l is not None:
                self.logger.debug("Setting limit for %s to %s" % (t.name, l))
                inp += self._format_cmd(self.cmds['set_limit'], task=t.name,
                                        limit='cpu.shares', value=l.shares)
            else:
                self.logger.debug("Skipping setting CPU limit for %s" % t.name)

        self.__call(inp=inp)

    def get_limits(self, tasks):
        for tname in tasks:
            self.logger.debug('Calling "%s %s %s %s %s %s"' % \
                              (self.exe, self.monitor_name, \
                               self.hierarchy, 'get', tname, 'shares'))
        return {}


    def delete(self, name):
        """ Delete a CPU cgroup """
        self.logger.debug("Removing task %s" % name)
        self._call('remove', task=name)
        self.logger.info("Removed task %s" % name)
