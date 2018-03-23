import sys

from cliff.app import App
#from cliff.commandmanager import CommandManager
from .commandmanager import MyCommandManager


class Cgmon(App):

    def __init__(self):
        super(Cgmon, self).__init__(
            description='cgmon client',
            version='0.1',
            #command_manager=CommandManager('cgmond.commands', convert_underscores=False),
            command_manager=MyCommandManager('cgmond.client.commands', convert_underscores=True),
            deferred_help=True,
            )

    def build_option_parser(self, description, version, argparse_kwargs=None):
        parser = super(Cgmon, self).build_option_parser(description, version, argparse_kwargs)
        parser.add_argument('-c', '--config', default='/path', type=str, help='Config file location')

        return parser

    def initialize_app(self, argv):
        self.LOG.debug('initialize_app')

    def prepare_to_run_command(self, cmd):
        # load config from self.config
        self.LOG.debug('prepare_to_run_command %s', cmd.__class__.__name__)

    def clean_up(self, cmd, result, err):
        self.LOG.debug('clean_up %s', cmd.__class__.__name__)
        if err:
            self.LOG.debug('got an error: %s', err)


def main(argv=sys.argv[1:]):
    cgmon = Cgmon()
    return cgmon.run(argv)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
