from collections import namedtuple
from cgmond.daemon.resources.interfaces import Policy

CPUWeight = namedtuple('CPUWeight', ['weight'])

class CPUWeightPolicy(Policy):
    def __init__(self):
        super(CPUWeightPolicy, self).__init__()

    def parse(self, expr):
        args = expr.split(',')
        for a in args:
            params = a.split('=')
            if params[0] != 'weight':
                continue
            # assert len(params) == 2
            weight = CPUWeight(int(params[1]))
            self.logger.debug("Found weight %s in expression \"%s\"" % (str(weight), expr))
            return weight

        self.logger.debug("No weight found in expr '%s'", expr)
        return None


    def calculate_limits(self, tasks, usage):
        limits = {}
        for tname in tasks:
            t = tasks[tname]
            limit_expr = t.limits.get('cpu', None)
            if not limit_expr:
                self.logger.debug("No CPU limit expression provided for task %s" % tname)
                continue
            cpuweight = self.parse(limit_expr)
            if cpuweight is None:
                self.logger.debug("No weight found in expr '%s' for task %s" % (limit_expr, tname))
                continue
            self.logger.debug("Found weight %s for task %s in expression \"%s\"" % (str(cpuweight), tname, limit_expr))

            limits[t.name] = CPULimit(cpuweight.weight * 10)

        return limits
