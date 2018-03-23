#!/usr/bin/python

import os
import daemon
import signal
import threading
import logging
import sys
import json
from lockfile import pidlockfile
from cgmond.utils import ensure_path
from collections import namedtuple
from functools import partial, update_wrapper
from resources import load_resources
from jsonrpclib.SimpleJSONRPCServer import SimpleJSONRPCServer
from config import MonitorConfig


class MonitorException(Exception):
    pass

App = namedtuple('App', ['name', 'limits', 'usage'])

def command(f):
    f.is_command = True
    return f


class Monitor(object):
    apps = None
    name = None
    limits = None
    config = None
    shutdown_event = None
    DEFAULT_LIMIT_NAME = '__DEFAULT'

    def __init__(self, monitor_name, config=None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.apps = {}
        self.name = monitor_name
        self.available_resources = load_resources()

        self.config = config
        self.limits = dict(self.config.limits)

        # self.resources = [self.available_resources[0](self)] + \
        self.resources = \
                    [resource_class(self,
                       policy=self.config.policies.get(resource_class.name.lower(), None),\
                       usage=self.config.usage.get(resource_class.name.lower(), None),\
                       limit=self.config.limit.get(resource_class.name.lower(), None))
                     for resource_class in self.available_resources
                     if resource_class.name.lower() in self.config.resources]

        self.limits[self.DEFAULT_LIMIT_NAME] = self._get_default_limit()

        for tname in self.resources[0].list_apps():
            # TODO find a way to restore previous limits ? Perhaps keep a
            # runtime file somewhere and reload it ?
            limit = self._get_default_limit()
            t = App(tname, limit, self._get_init_usage())

            self.apps[tname] = t

    def _get_init_usage(self):
        """
        Return a usage structure representing no usage measurement.
        """

        usage = {}
        for r in self.resources:
            usage[r.name] = None

        return usage

    def _get_default_limit(self):
        """
        Return a limit structure representing default limits.
        """

        limits = {}
        for r in self.resources:
            limits[r.name] = ''

        return limits


    def _new_app(self, name, limit_name):
        """
        Return a new App structure.
        """

        if self.apps.get(name, None) is not None:
            raise MonitorException("App '%s' already exists" % name)

        if limit_name is None:
            limit_name = self.DEFAULT_LIMIT_NAME

        limit = self.limits.get(limit_name, None)
        if limit is None:
            raise MonitorException("No policy '%s' found" % limit_name)

        return App(name, limit, self._get_init_usage())


    def _prepare_add(self, app, new_limits):
        """
        Prepare the addition of a new monitored app.

        In order to successfully add a new monitored app, we must create
        every cgroup directory and set the appropriate limits before
        spawning or attaching the new process. This way, when the app is
        added, it cannot escape the calculated limits.
        """

        name = app.name

        # create the directories and set any limits
        for r in self.resources:
            r.create(name)

            # if no policy is selected, then we cannot set any limits
            if not r.policy:
                continue

            limit = new_limits.get(name, None)
            if limit is not None:
                r.set_limit(name, limit)


    def calculate_limits(self, apps):
        """
        Given a set of Apps, calculate limits to be enforced.
        """

        new_scores = {}
        new_limits = {}
        for r in self.resources:
            if not r.policy:
                continue
            limits = r.policy.calculate_limits_from_apps(apps)
            score, limits = r.policy.calculate_score_and_limits_from_apps(apps)
            new_scores[r.name] = score
            new_limits[r.name] = limits

        return new_scores, new_limits


    def calculate_score(self, apps):
        """
        Given a set of Apps, calculate limits to be enforced.
        """

        new_scores = {}
        for r in self.resources:
            if not r.policy:
                continue
            score =  r.policy.calculate_score_from_apps(apps)
            new_scores[r.name] = score

        return new_scores


    def apply_limits(self, limits):
        """
        Apply the given limits for each resource and for each app.
        """

        for r in self.resources:
            if not r.policy:
                continue
            if limits.get(r.name, None) is None:
                continue
            r.set_limits(self.apps, limits[r.name])



    def update_usages(self):
        for r in self.resources:
            usages = r.get_usage(self.apps)
            if usages is None:
                continue
            for tname in self.apps:
                t = self.apps[tname]
                if usages.get(t.name, None) is not None:
                    t.usage[r.name] = usages[t.name]


    def print_apps(self):
        for tname in self.apps:
            print ""
            t = self.apps[tname]
            print "App: ", t.name
            print "  Limits:"
            for r in t.limits:
                print "    ", r, ":", t.limits[r]
            print "  Usage:"
            for r in t.usage:
                print "    ", r, ":", t.usage[r]




    @command
    def app_spawn(self, name, limit, process, args, force=False):
        """
        Spawn a new monitored process.
        """

        def spawn_process(process, args):
            """
            Spawn the requested process detached from the parent process.

            This uses the daemon module. Using the daemon module to detach from
            the parent process, the calling process exits. To avoid that, we
            permorm another fork at the beginning.
            """

            p = os.fork()
            if p == 0:
                logpath = os.path.join(self.config.workdir, name)
                ensure_path(logpath)
                # TODO err check
                sout = open(os.path.join(logpath, 'stdout.log'), 'a+')
                serr = open(os.path.join(logpath, 'stderr.log'), 'a+')

                ctx = daemon.DaemonContext(detach_process=True,
                        stdout=sout, stderr=serr)
                # defaults
                # umask=0o000
                # working_directory = '/'
                # uid = os.getuid()
                # gid = os.getgid()
                # TODO maybe we want to set uid/gid on app spawn

                pid = os.getpid()
                for r in self.resources:
                    r.add(name, pid)

                with ctx:
                    os.execvp(process, [process] + args)

            # TODO catch any errors while executing the process
            os.waitpid(p, 0)

        t = self._new_app(name, limit)

        apps = dict(self.apps)
        apps[t.name] = t

        new_scores, new_limits = self.calculate_limits(apps)
        neg_scores = {}
        for r, s in new_scores.iteritems():
            if float(s) < 0:
                neg_scores[r] = s

        for r, s in neg_scores.iteritems():
            if force:
                self.logger.info("Ignoring negative score %s for resource %s "
                                 "while spawning '%s' with policy '%s'." %
                                 (s, r, name, limit))
            else:
                self.logger.warn("Resource %s returned negative score (%s) "
                                 "while spawning '%s' with policy '%s'." %
                                 (r, s, name, limit))

        if len(neg_scores) > 0 and not force:
            raise MonitorException("Resources '%s' returned negative scores" %
                                   ','.join([r for r in neg_scores.iterkeys()]))

        self._prepare_add(t, new_limits)

        spawn_process(process, args)

        self.apps[t.name] = t

        self.apply_limits(new_limits)



    @command
    def app_attach(self, name, pid, limit_name):
        """
        Attach a pid to a given named policy
        """

        t = self._new_app(name, limit_name)

        apps = dict(self.apps)
        apps[t.name] = t
        new_scores, new_limits = self.calculate_limits(apps)
        self._prepare_add(t, new_limits)

        for r in self.resources:
            r.add(name, pid)

        self.apps[t.name] = t
        self.apply_limits(new_limits)


    @command
    def app_list(self):
        class CustomEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, object):
                    return obj.__dict__

                return json.JSONEncoder.default(self, obj)

        return json.dumps(self.apps, cls=CustomEncoder)


    @command
    def remove(self, name):
        """
        Callback when all of app's processes have exited.

        Using the release agent cgroup mechanism, when all of app's processes
        have exited, the monitor gets notified of the event to perform any
        cleanup and/or limit recalculation.
         """

        # t = App(name, self.limits[name], self._get_init_usage())
        # new_limits = self._prepare_add(t)

        if self.apps.get(name, None) is None:
            raise MonitorException("No app '%s' found" % name)

        for r in self.resources:
            r.remove_app(name)

        del self.apps[name]

        # recalculate limits
        new_scores, new_limits = self.calculate_limits(self.apps)
        self.apply_limits(new_limits)


    @command
    def limit_create(self, limit_name, limit):
        """
        Create a new limit.
        """

        if self.limits.get(limit_name, None) is not None:
            raise MonitorException("Limit '%s' already exists" % limit_name)

        # TODO validate expression
        self.limits[limit_name] = self.config.parse_limit(limit)


    @command
    def limit_list(self):
        """
        Return a list of the available limits.
        """

        return self.limits


    @command
    def limit_apply(self, app_name, limit_name, force=False):
        """
        Apply a limit to a app.
        """

        t = self.apps.get(app_name, None)
        if t is None:
            raise MonitorException("No app '%s' found" % app_name)

        l = self.limits.get(limit_name, None)
        if l is None:
            raise MonitorException("No policy '%s' found" % limit_name)

        apps = dict(self.apps)
        t = App(t.name, l, t.usage)
        apps[t.name] = t

        # calculate limits to see if they can be enforced
        new_scores, new_limits = self.calculate_limits(apps)
        neg_scores = {}
        for r, s in new_scores.iteritems():
            if float(s) < 0:
                neg_scores[r] = s

        for r, s in neg_scores.iteritems():
            if force:
                self.logger.info("Ignoring negative score %s for resource %s "
                                 "while applying policy '%s' to app '%s'." %
                                 (s, r, limit_name, app_name))
            else:
                self.logger.warn("Resource %s returned negative score (%s) "
                                 "while applying policy '%s' to app '%s'." %
                                 (r, s, limit_name, app_name))

        if len(neg_scores) > 0 and not force:
            raise MonitorException("Resources '%s' returned negative scores" %
                                   ','.join([r for r in neg_scores.iterkeys()]))


        self.apps[t.name] = t
        self.apply_limits(new_limits)

    @command
    def resource_list(self):
        return [r.name for r in self.resources[1:]]

    @command
    def stop(self):
        self.shutdown_event.set()

    @command
    def kill(self):
        self.shutdown_event.set()


class MonitorServer(object):
    monitor = None
    server = None
    logger = None

    def __init__(self, monitor):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.monitor = monitor


    def _register_func(self, func):

        def wrap(fun, *args, **kwargs):
            try:
                return True, fun(*args, **kwargs)
            except Exception as e:
                if isinstance(e, MonitorException):
                    return False, e.message
                else:
                    import traceback
                    self.logger.error("%s" % traceback.format_exc())
                    raise e

        partial_func = partial(wrap, func)
        update_wrapper(partial_func, func)
        self.server.register_function(partial_func)

    def start(self):
        self.logger.info("Starting...")
        self.server = SimpleJSONRPCServer(('localhost', 8080), logRequests=False)

        for maybeCommand in self.monitor.__class__.__dict__.values():
            if hasattr(maybeCommand, 'is_command'):
                command_name = maybeCommand.__name__
                self.logger.debug("Registering command %s" % command_name)
                command = getattr(self.monitor, command_name)
                self._register_func(command)


    def stop(self):
        if self.server:
            self.logger.info("Stopping server")
            self.server.shutdown()
            self.server.server_close()


    def serve_forever(self):
        self.logger.info("Entering  main loop")
        self.server.serve_forever()



class MonitorDaemon(object):
    server = None
    server_thread = None
    shutdown_event = None
    monitor = None

    def __init__(self, monitor):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.monitor = monitor
        self.shutdown_event = threading.Event()
        self.shutdown_event.clear()
        self.server = MonitorServer(monitor)

        self.monitor.shutdown_event = self.shutdown_event

    def run_forever(self):
        self.server.start()
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.start()

        try:
            while not self.shutdown_event.is_set():
                # self.monitor.update_usages()
#                self.monitor.print_apps()
                self.shutdown_event.wait(2)
        except KeyboardInterrupt:
            self.logger.info("Exiting...")

        finally:
            self.shutdown_event.set()
            self.server.stop()
            self.server_thread.join()



def start_daemon(args):

    def sigterm(d, signum, stackframe):
        d.shutdown_event.set()

    conffile = '/root/code/cgroups-monitor-daemon/config'
    if args.config is not None:
        conffile = args.config


    config = MonitorConfig(conf_file=conffile)
    config.load()

    ensure_path(config.workdir)

    detach = True
    if args.foreground:
        detach = False


    logger = logging.getLogger('')
    logger.setLevel(logging.DEBUG)

    # create console handler and set level to debug

    if detach:
        logfile = os.path.join(config.workdir, config.name + '.log')
        h = logging.FileHandler(logfile)
        h.setLevel(logging.DEBUG)
        # logging.basicConfig(filename=logfile, level=logging.DEBUG)
    else:
        h = logging.StreamHandler()
        h.setLevel(logging.DEBUG)
        # logging.basicConfig(level=logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s:%(levelname)s: %(message)s')
    h.setFormatter(formatter)
    logger.addHandler(h)

    m = Monitor(config.name, config=config)

    d = MonitorDaemon(m)
    on_terminate = partial(sigterm, d)

    pidfile_path = os.path.join(config.workdir, config.name + '.pid')
    ctx = daemon.DaemonContext(umask=0o002,
                pidfile=pidlockfile.PIDLockFile(pidfile_path),
                detach_process=detach,
                files_preserve=[h.stream],
                # TODO fix this
                stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)

    ctx.signal_map = {
        signal.SIGTERM: on_terminate,
    }

    with ctx:
        d.run_forever()



def parse_args():
    import argparse
    parser = argparse.ArgumentParser(description='CGmon daemon')

    parser.add_argument('-c', '--config', type=str, help='Path to config file')
    parser.add_argument('-f', '--foreground', action='store_true',
                        help='Keep to foreground')

    return parser.parse_args()

def entry_point():
    start_daemon(parse_args())

if __name__ == '__main__':
    entry_point()
