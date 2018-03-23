from collections import namedtuple
from cgmond.daemon.resources.interfaces import Policy
# from cgmond.daemon.resources.cpu.cpu import CPULimit

CPULimit = namedtuple('CPULimit', ['shares'])
CPULimits = namedtuple('CPULimits', ['min', 'target'])

class CPULimitPolicy(Policy):
    def __init__(self, resource_name):
        super(CPULimitPolicy, self).__init__()
        self.resource_name = resource_name

    def _parse(self, expr):
        args = expr.split(',')
        for a in args:
            params = a.split('=')
            if params[0] != 'limit':
                continue
            # assert len(params) == 2
            limits = params[1].split(':')
            # assert len(limits) == 3
            min = int(limits[0])
            target = int(limits[1])
            # assert 0 < min,target <= 100
            limit = CPULimits(min, target)

            self.logger.info("Found limit %s" % str(limit))
            return limit

        self.logger.info("No limit found in expr '%s'", expr)
        return None


    def _extract_cpulimits(self, limit_expressions):
        cpulimits = {}
        for tname in limit_expressions:
            limit_expr = limit_expressions.get(tname, None)
            if not limit_expr:
                continue
            limits = self._parse(limit_expr)
            if limits is None:
                continue
            cpulimits[tname] = limits

        return cpulimits

    def _calculate_score_and_limits(self, cpulimits, calc_limits=True):
        sum_min = 0
        sum_target = 0

        for tname in cpulimits:
            l = cpulimits[tname]
            sum_min += l.min
            sum_target += l.target

        limits = {}
        if sum_min > 100 :
            score = -float(sum_min)/100.0
            if calc_limits:
                for tname in cpulimits:
                    l = cpulimits[tname]
                    limits[tname] = CPULimit(10 * l.min)
        elif sum_target <= 100 :
            score = 1.0 + (100.0 - float(sum_target))/100.0
            # All tasks can have their target CPU limit or above
            # Excess will be distributed relative to the l.target
            # The higher the target value, the more CPU they will get
            if calc_limits:
                for tname in cpulimits:
                    l = cpulimits[tname]
                    limits[tname] = CPULimit(10 * l.target)
        else:
            # sum_min < 100 and sum_target > 100
            excess = 100 - sum_min
            score = float(excess)/100.0
            if calc_limits:
                for tname in cpulimits:
                    l = cpulimits[tname]
                    limits[tname] = CPULimit(10 * l.min + (10 * (l.target - l.min) * excess)/(sum_target - sum_min))

        self.logger.info("Calculated score %.2f" % score)

        return score, limits


    def calculate_score(self, limit_expressions, usage):
        cpulimits = self._extract_cpulimits(limit_expressions)

        score, _ = self._calculate_score_and_limits(cpulimits,
                                                    calc_limits = False)

        return score



    def calculate_limits(self, limit_expressions, usage):
        cpulimits = self._extract_cpulimits(limit_expressions)

        _, limits = self._calculate_score_and_limits(cpulimits)

        return limits
