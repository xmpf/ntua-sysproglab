import logging
from cliff.command import Command
import subprocess
import json
import os
from cgmond.client.daemoncontrol import DaemonControl, DaemonControlException
from cgmond.utils import ensure_path
from cgmond.client.utils import servercmd

DEFAULT_WORKDIR='/tmp/wd'
DEFAULT_NAME='monitor'

def get_pidfile_path(wd, name):
    return os.path.join(wd, name, name + '.pid')

class Daemon_start(Command):
    """ Start a new daemon """

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(Daemon_start, self).get_parser(prog_name)
        parser.add_argument('-w', '--workdir', default=DEFAULT_WORKDIR, type=str, help='workdir help')
        parser_required_named = parser.add_argument_group('required named arguments')
        parser_required_named.add_argument('-p', '--policy',  required=True, type=str, help='policy module help')
        parser_required_named.add_argument('-l', '--limit',  required=True, type=str, help='limit module help')

        return parser


    def take_action(self, parsed_args):
        cfg = {
            'name': DEFAULT_NAME,
            'workdir': DEFAULT_WORKDIR,
            "resources": ["monitor", "cpu"],
            "policies": {
                "cpu": {"name": "external",
                        "executable": "cgmon-policy-external"
                       }
                },
            "limit": {
                    "monitor": {"name": "limit"
                            },
                    "cpu": {"name": "external",
                            "executable": "cgmon-cgroup-external"
                            }
                },
            "limits": {
                "default_min100" : "--cpu 100",
                "default_min500" : "--cpu 500",
                "default_min1000" : "--cpu 1000"
            }
        }

        cfg['workdir'] = parsed_args.workdir
        cfg['policies']['cpu']['executable'] = parsed_args.policy
        cfg['limit']['cpu']['executable'] = parsed_args.limit

        ensure_path(parsed_args.workdir)
        cfg_path = os.path.join(parsed_args.workdir, 'cfg')
        json.dump(cfg, open(cfg_path, 'w'))


        try:
            os.stat(parsed_args.policy)
        except OSError:
            raise Exception("Policy module '%s' not found" % parsed_args.policy)

        try:
            os.stat(parsed_args.limit)
        except OSError:
            raise Exception("Limit module '%s' found" % parsed_args.limit)


        def start_fn(cfg_path):
            CGMOND = 'cgmond'
            CGMOND_ARGS = ['-c', cfg_path]

            subprocess.check_call([CGMOND]+ CGMOND_ARGS)

            return True

        pidfile_path = get_pidfile_path(cfg['workdir'], cfg['name'])
        dc = DaemonControl(pidfile_path=pidfile_path, start_fn=start_fn)

        msg = "{:25}".format("Server starting...")
        self.app.stdout.write(msg)
        self.app.stdout.flush()

        try:
            dc.start(cfg_path)
            self.app.stdout.write("OK\n")
        except DaemonControlException:
            self.app.stdout.write("ERROR\n")
            raise


class Daemon_stop(Command):
    """ Stop a running daemon """

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(Daemon_stop, self).get_parser(prog_name)
        parser.add_argument('-w', '--workdir', default=DEFAULT_WORKDIR, type=str, help='workdir help')

        return parser


    def take_action(self, parsed_args):
        def stop_fn():
            servercmd('stop')


        pidfile_path = get_pidfile_path(parsed_args.workdir, DEFAULT_NAME)
        dc = DaemonControl(pidfile_path=pidfile_path, stop_fn=stop_fn)

        msg = "{:25}".format("Server stopping...")
        self.app.stdout.write(msg)
        self.app.stdout.flush()

        try:
            dc.stop()
            self.app.stdout.write("OK\n")
            # self.app.stdout.flush()
        except DaemonControlException:
            self.app.stdout.write("ERROR\n")
            raise


class Daemon_kill(Command):
    """ Kill a running daemon """

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(Daemon_kill, self).get_parser(prog_name)
        parser.add_argument('-w', '--workdir', default=DEFAULT_WORKDIR, type=str, help='workdir help')

        return parser

    def take_action(self, parsed_args):
        pidfile_path = get_pidfile_path(parsed_args.workdir, DEFAULT_NAME)
        dc = DaemonControl(pidfile_path=pidfile_path)
        msg = "{:25}".format("Killing server...")
        self.app.stdout.write(msg)
        self.app.stdout.flush()

        try:
            dc.stop()
            self.app.stdout.write("OK\n")
            # self.app.stdout.flush()
        except DaemonControlException:
            self.app.stdout.write("ERROR\n")
            raise


class Daemon_status(Command):
    """ Show status of daemon """

    log = logging.getLogger(__name__)

    # def get_parser(self, prog_name):
    #     parser = super(Daemon_kill, self).get_parser(prog_name)
    #     parser_required_named = parser.add_argument_group('required named arguments')

    def get_parser(self, prog_name):
        parser = super(Daemon_status, self).get_parser(prog_name)
        parser.add_argument('-w', '--workdir', default=DEFAULT_WORKDIR, type=str, help='workdir help')

        return parser

    def take_action(self, parsed_args):
        pidfile_path = get_pidfile_path(parsed_args.workdir, DEFAULT_NAME)
        dc = DaemonControl(pidfile_path=pidfile_path)
        if dc.status():
            self.app.stdout.write("Server running\n")
        else:
            self.app.stdout.write("Server not running\n")
