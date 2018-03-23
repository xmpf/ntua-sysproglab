import logging
import jsonrpclib
from cliff.command import Command
from cliff.lister import Lister


class Module_enable(Command):
    """ Enable a module to a given resource """

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(Module_enable, self).get_parser(prog_name)
        parser_required_named = parser.add_argument_group('required named arguments')
        parser_required_named.add_argument('-r', '--resource',  type=str, required=True, help='resource help')
        parser_required_named.add_argument('-m', '--module', type=str, required=True, help='policy name')
        # TODO module args

        return parser


    def take_action(self, parsed_args):
        jsonrpclib.config.version = 1.0
        server = jsonrpclib.Server('http://localhost:8080')

        return server.module_enable()


class Module_list(Lister):
    """ List available modules """

    log = logging.getLogger(__name__)


    def get_parser(self, prog_name):
        parser = super(Module_list, self).get_parser(prog_name)
        parser.add_argument('-r', '--resource',  type=str, help='resource help')

        return parser


    def take_action(self, parsed_args):
        jsonrpclib.config.version = 1.0
        server = jsonrpclib.Server('http://localhost:8080')

        return server.module_list()
