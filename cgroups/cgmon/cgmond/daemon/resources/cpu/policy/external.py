from cgmond.daemon.resources.interfaces import Policy
from cgmond.utils import check_output
from collections import namedtuple
from cStringIO import StringIO
from cgmond.scripts.util import load_tabular_data

CPULimit = namedtuple('CPULimit', ['shares'])


# TODO cleanup
class ExternalPolicy(Policy):
    exe = '/root/code/cgroups-monitor-daemon/cgmond/ex.py'

    def __init__(self, resource_name, executable=None, **kwargs):
        super(ExternalPolicy, self).__init__(resource_name, **kwargs)
        if executable is not None:
            self.exe = executable

        self.logger.debug("Using executable '%s'" % self.exe)


    def _call(self, limit_input):
        self.logger.debug("Calling %s with input %s" % (self.exe, limit_input.replace('\n', '\\n')))
        output, error = check_output(self.exe, [], inp=limit_input)
        if output is not None:
            self.logger.debug("Got output: %s" % (output.replace('\n', '\\n')))
        else:
            self.logger.debug("Returned not output")

        data = load_tabular_data(StringIO(output), separator=':')
        score = data[0][1]
        limits = {}

        if len(data) > 1:
            for d in data[1:]:
                limits[d[1]] = CPULimit(int(d[3]))


        return score, limits


    def _extract_input(self, limit_expressions):
        limit_input = ""
        for tname in limit_expressions:
            limit_expr = limit_expressions.get(tname, None)
            if not limit_expr:
                continue
            li = 'policy{sep}{task}{sep}{resource}{sep}{policy}\n'
            li = li.format(sep=':', task=tname, resource='cpu',
                           policy=limit_expr)
            limit_input += li

        return limit_input


    def calculate_score(self, limit_expressions, usage):
        inp = self._extract_input(limit_expressions)
        score, _ = self._call(inp)

        return score


    def calculate_limits(self, limit_expressions, usage):
        inp = self._extract_input(limit_expressions)
        _, limits = self._call(inp)
        self.logger.debug("Calculated limits %s", limits)

        return limits


    def calculate_score_and_limits(self, limit_expressions, usage):
        inp = self._extract_input(limit_expressions)
        score, limits = self._call(inp)
        self.logger.debug("Calculated limits %s", limits)

        return score, limits
