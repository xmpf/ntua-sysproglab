
from cgmond.daemon.resources.interfaces import Limit
from cgmond.utils import check_output


class ExternalLimit(Limit):
    hierarchy = 'monitor'
    exe = 'cgmon-cgroup-external'
    separator = ':'
    input_prefix = '{sep}{monitor}{sep}{hierarchy}{sep}'
    cmds = {
        'create': 'create' + input_prefix + '{task}\n',
        'add': 'add' + input_prefix + '{task}{sep}{pid}\n',
        'set_limit': 'set_limit' + input_prefix + '{task}{sep}{limit}{sep}{value}\n',
        'get_limit': 'get_limit' + input_prefix + '{task}{sep}{limit}\n',
        'remove': 'remove' + input_prefix + '{task}\n',
    }


    def __init__(self, monitor_name, executable=None, **kwargs):
        super(ExternalLimit, self).__init__(monitor_name, **kwargs)
        if executable is not None:
            self.exe = executable
        self.logger.debug("Using executable '%s'" % self.exe)


    def _format_cmd(self, c, **kwargs):
        return c.format(sep=self.separator, hierarchy=self.hierarchy,
                        monitor=self.monitor_name, **kwargs)


    def __call(self, inp=""):
        self.logger.debug("Calling %s with input %s" % (self.exe, inp.replace('\n', '\\n')))
        return check_output(self.exe, [], inp=inp)


    def _call(self, cmd, **kwargs):
        inp = self._format_cmd(self.cmds[cmd], **kwargs)
        return self.__call(inp=inp)


    def create(self, name):
        """ Initialize Monitor cgroup for task """

        self.logger.debug("Creating Monitor cgroup for %s" % name)
        self._call('create', task=name)
        self.logger.info("Created Monitor cgroup for %s" % name)


    def add(self, name, pid):
        """ Add a given pid in the Monitor cgroup of the task """

        self.logger.debug("Adding %d in Monitor cgroup for %s" % (pid, name))
        self._call('add', task=name, pid=pid)
        self.logger.info("Added %d in Monitor cgroup for %s" % (pid, name))


    def delete(self, name):
        """ Delete a Monitor cgroup """

        self.logger.debug("Removing task %s" % name)
        self._call('remove', task=name)
        self.logger.info("Removed task %s" % name)
