
import logging
from cgmond.daemon.cgroup import MonitorCgroup
from cgmond.daemon.resources import load_policies, load_limit, load_usage


def format_unexpected_kwargs(kwargs):
        unexp = ""

        for k, v in kwargs.iteritems():
            unexp += "'%s': '%s'," % (k, v)

        return unexp.rstrip(',')


class Limit(object):
    logger = None
    monitor_name = None

    def __init__(self, resource, **kwargs):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.monitor_name = resource.monitor.name
        if len(kwargs) > 0:
            self.logger.warning("Got unexpected arguments: %s" % \
                                format_unexpected_kwargs(kwargs))


    def create(self, name):
        raise NotImplementedError


    def add(self, name, pid):
        raise NotImplementedError


    def list(self, empty=False):
        raise NotImplementedError


    def delete(self, names):
        raise NotImplementedError


    # {name: {limit: value} }
    # def set_limits(self, limits)
    #     raise NotImplementedError
    # def set_limit(self, name, limit_name, value):
    #     return self.set_limit({name: {limit_name: value}})

    # return {name: {limit: value} }
    # def get_limits(self, limits)
    #     raise NotImplementedError
    # def get_limit(self, name, limit_name):
    #     l = self.get_limit({name: [limit_name]})
    #     return l[name][limit_name]

    def set_limit(self, name, limit_name, value):
        raise NotImplementedError


    def get_limit(self, name, limit_name):
        raise NotImplementedError


class Policy(object):
    logger = None
    resource_name = None

    def __init__(self, resource, **kwargs):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.resource_name = resource.name
        if len(kwargs) > 0:
            self.logger.warning("Got unexpected arguments: %s" % \
                              format_unexpected_kwargs(kwargs))


    def calculate_score(self, limit_expressions, usage):
        """
        Calculate new resource score.

        Given a dictionary with limit expressions and a dictionary with
        resource usage, calculate the resource's score.
        """

        raise NotImplementedError


    def calculate_limits(self, limit_expressions, usage):
        """
        Calculate new limits and new resource score.

        Given a dictionary with limit expressions and a dictionary with
        resource usage, return the resource's specific limits needed to enforce
        the selected policy
        """

        raise NotImplementedError


    def calculate_score_and_limits(self, limit_expressions, usage):
        """
        Calculate new limits and new resource score.

        Given a dictionary with limit expressions and a dictionary with
        resource usage, return the resource's specific limits needed to enforce
        the selected policy
        """

        raise NotImplementedError


    def _extract_limits_and_usage(self, apps):
        """
        Extract limit expressions and usage for the instance's resource.
        """

        limit_exprs = {}
        usages = {}

        rname = self.resource_name.lower()
        for tname in apps:
            t = apps[tname]
            limit_expr = t.limits.get(rname, None)
            if not limit_expr:
                continue
            limit_exprs[tname] = limit_expr

            usage = t.usage.get(rname, None)
            usages[tname] = usage

        return limit_exprs, usages

    def calculate_score_from_apps(self, apps):
        """
        Calculate score given a dictionary of apps.

        Extract limit expressions and usage for the instance's resource and
        use the policy to calculate the new score.
        """

        limit_exprs, usages= self._extract_limits_and_usage(apps)
        return self.calculate_score(limit_exprs, usages)


    # TODO Maybe this does not belong here
    def calculate_limits_from_apps(self, apps):
        """
        Calculate limits given a dictionary of apps.

        Extract limit expressions and usage for the instance's resource and
        use the policy to calculate new limits to be enforced.
        """

        limit_exprs, usages= self._extract_limits_and_usage(apps)
        return self.calculate_limits(limit_exprs, usages)


    def calculate_score_and_limits_from_apps(self, apps):
        """
        Calculate score and limits given a dictionary of apps.

        Extract limit expressions and usage for the instance's resource and
        use the policy to calculate new score and new limits to be enforced.
        """

        limit_exprs, usages= self._extract_limits_and_usage(apps)
        return self.calculate_score_and_limits(limit_exprs, usages)


class Resource(object):
    logger = None
    monitor = None
    name = None
    hierarchy = None
    policy = None
    usage = None
    limit = None
    policy_submodules = None
    usage_submodules = None
    policy_submodules = None

    def __init__(self, monitor, policy, usage, limit):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.monitor = monitor
        #import inspect
        #print inspect.getfile(self.__class__)
        self.policy_submodules = load_policies(self.name)
        self.logger.debug("Loaded policy submodules: %s", [p for p in self.policy_submodules])

        self.usage_submodules = load_usage(self.name)
        self.logger.debug("Loaded usage submodules: %s", [u for u in self.usage_submodules])

        self.limit_submodules = load_limit(self.name)
        self.logger.debug("Loaded limit submodules: %s", [l for l in self.limit_submodules])


        self._load_policy(policy)
        self._load_usage(usage)
        self._load_limit(limit)

        # self.limit.create("")


    def _load_submodule(self, submodule, config, default):
        """
        Load a submodule with a given config.
        """
        if config is None:
            config = {}
            module_name = default
            if default is None:
                return
        else:
            config = dict(config)
            module_name = config['name']
            del config['name']

        if module_name not in getattr(self, submodule + '_submodules'):
            # TODO ERROR
            pass

        submodules = getattr(self, submodule + '_submodules')
        module = submodules[module_name](self, **config)
        setattr(self, submodule, module)

        self.logger.debug("Using %s submodule '%s'", submodule, module_name)


    def _load_policy(self, policy_config):
        self._load_submodule('policy', policy_config, self.default_policy)


    def _load_usage(self, usage_config):
        self._load_submodule('usage', usage_config, self.default_usage)


    def _load_limit(self, limit_config):
        self._load_submodule('limit', limit_config, self.default_limit)


    def create(self, name):
        """ Initialize name """
        raise NotImplementedError

    def add(self, name, pid):
        """ Add a given pid in the hierarchy's limit of the named app """
        raise NotImplementedError

    def set_limit(self, name, limit):
        """ Set a hierarchy specific limit to a named app """
        raise NotImplementedError

    def get_limits(self):
        raise NotImplementedError

    def set_limits(self, apps, limits):
        raise NotImplementedError

    def get_usage(self, apps):
        raise NotImplementedError

    def remove_app(self, app):
        raise NotImplementedError

    def get_resource_usage(self):
        raise NotImplementedError

    def list_apps(self):
        raise NotImplementedError


class ResourceCgroup(object):
    mcg = None
    hierarchy = None

    def __init__(self, hierarchy, monitor_name):
        self.mcg = MonitorCgroup(hierarchy, monitor_name)


    def create(self, name):
        self.mcg.create(name)


    def add(self, name, pid):
        self.mcg.add(name, pid)


    def list(self, empty=False):
        return self.mcg.list(empty=empty)


    def delete(self, name):
        self.mcg.delete(name)


    def set_limit(self, name, limit_name, value):
        self.mcg.set_limit(name, limit_name, value)


    def get_limit(self, name, limit_name):
        return self.mcg.get_limit(name, limit_name)


class Usage(object):
    logger = None
    monitor_name = None

    def __init__(self, resource, **kwargs):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.monitor_name = resource.monitor.name
        if len(kwargs) > 0:
            self.logger.warning("Got unexpected arguments: %s" % \
                              format_unexpected_kwargs(kwargs))


    def get_usage(self, apps=None):
        raise NotImplementedError


    def get_total_usage(self):
        raise NotImplementedError


    def get_toal_available(self):
        raise NotImplementedError


    def app_create(self, app):
        raise NotImplementedError


    def app_add(self, app, pid):
        raise NotImplementedError


    def app_remove(self, app):
        raise NotImplementedError
