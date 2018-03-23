import json
import os

CONFIG_DEFAULTS = {
    'workdir': '/tmp',
    'name': 'testmonitor',
    'logfile': None,
    'limits': {},
    'resources': {},
    'policies': {},
    'usage': {},
    'limit': {},
}

class MonitorConfig(object):
    _config = None

    conf_file = None

    # uid = None
    # gid = None

    def __init__(self, conf_file=None):
        self._config = dict(CONFIG_DEFAULTS)
        self.conf_file = conf_file

    def load(self):
        if self.conf_file is None:
            return

        with open(self.conf_file, 'r') as f:
            config = f.read()

        self._config.update(json.loads(config))
        limit_exprs = self._config.get('limits', None)
        if limit_exprs is not None:
            self._config['limits'] = self.parse_limits(limit_exprs)

        self._config['resources'] = [r.lower() for r in self._config['resources']]
#        self._config['policies'] = {r.lower(): self._config['policies'][r].lower() for r in self._config['policies']}
        self._config['policies'] = {r.lower(): self._config['policies'][r] for r in self._config['policies']}
        self._config['usage'] = {r.lower(): self._config['usage'][r] for r in self._config['usage']}
        self._config['limit'] = {r.lower(): self._config['limit'][r] for r in self._config['limit']}

    # TODO Static method ?
    def parse_limit(self, expr):
        limits = {}
        if not expr.startswith('--'):
            # parse error
            return limits

        while len(expr) > 0:
            start = len('--')
            next = expr.find('--', start)
            if next == -1:
                next = len(expr)
            next_limit = [x.strip() for x in expr[start:next].strip().split(' ', 1)]
            if len(next_limit) != 2:
                # parse error
                break
            resource, limit = next_limit
            limits[resource] = limit
            expr = expr[next:]

        return limits


    # TODO Static method ?
    def parse_limits(self, limit_exprs):
        """
        Parse limits found in configuration file.
        """

        limits = {}
        if not limit_exprs:
            return limits

        for limit_name in limit_exprs:
            expr = limit_exprs[limit_name].strip()
            limits[limit_name] = self.parse_limit(expr)

        return limits

    @property
    def workdir(self):
        return os.path.join(self._config['workdir'], self.name)

    @property
    def limits(self):
        return self._config['limits']

    @property
    def resources(self):
        return self._config['resources']

    @property
    def policies(self):
        return self._config['policies']

    @property
    def usage(self):
        return self._config['usage']

    @property
    def limit(self):
        return self._config['limit']

    @property
    def name(self):
        return self._config['name']

    @property
    def logfile(self):
        return self._config['logfile']
