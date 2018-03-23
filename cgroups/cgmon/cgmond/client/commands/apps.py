import logging
from cliff.command import Command
from cliff.lister import Lister
from cgmond.client.utils import servercmd
import shlex


class App_spawn(Command):
    """ Spawn a new app """

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(App_spawn, self).get_parser(prog_name)
        parser_required_named = parser.add_argument_group('required named arguments')
        parser_required_named.add_argument('-n', '--name',  required=True, type=str, help='name help')
        parser_required_named.add_argument('-e', '--remote_command', required=True, type=str, help='command help')
        parser.add_argument('-p', '--policy',  type=str, help='command help', default=None)
        parser.add_argument('-f', '--force',  action='store_true', help='Force spawn even if app does not fit')

        return parser


    def take_action(self, parsed_args):
        cmd = shlex.split(parsed_args.remote_command)

        return servercmd('app_spawn', parsed_args.name, parsed_args.policy,
                         cmd[0], cmd[1:], parsed_args.force)


class App_list(Lister):
    """ List running apps """

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        apps = servercmd('app_list')

        import json
        apps = json.loads(apps)
        columns = (['App'])
        values = []
        for k in apps.iterkeys():
            values.append((k,))

        if len(values) == 0:
            values = [("No apps",)]

        return (columns, values)



class App_attach(Command):
    """ Attach a process to a app """

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(App_attach, self).get_parser(prog_name)
        parser_required_named = parser.add_argument_group('required named arguments')
        parser_required_named.add_argument('-n', '--name',  required=True, type=str, help='name help')
        parser_required_named.add_argument('-t', '--app-pid',  required=True, type=int, help='pid help')
        parser_required_named.add_argument('-p', '--policy', type=str, help='command help', default=None, required=False)

        return parser


    def take_action(self, parsed_args):

        return servercmd('app_attach', parsed_args.name, parsed_args.app_pid,
                         parsed_args.policy)
