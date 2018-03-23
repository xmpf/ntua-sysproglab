import logging
from cliff.command import Command
from cliff.lister import Lister
from cgmond.client.utils import servercmd


class Policy_create(Command):
    """ Create a new policy """

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(Policy_create, self).get_parser(prog_name)
        parser_required_named = parser.add_argument_group('required named arguments')
        parser_required_named.add_argument('-n', '--name',  required=True, type=str, help='name help')
        parser_required_named.add_argument('-p', '--policy',  type=str, help='policyhelp', required=True)

        return parser


    def take_action(self, parsed_args):
        return servercmd('limit_create', parsed_args.name, '--cpu ' +
                         parsed_args.policy)


class Policy_apply(Command):
    """ Apply a policy to a task """

    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(Policy_apply, self).get_parser(prog_name)
        parser_required_named = parser.add_argument_group('required named arguments')
        parser_required_named.add_argument('-t', '--task',  required=True, type=str, help='name help')
        parser_required_named.add_argument('-p', '--policy',  required=True, type=str, help='policy help')
        parser.add_argument('-f', '--force',  action='store_true', help='Force apply even if policy does not fit')

        return parser

    def take_action(self, parsed_args):
         return servercmd('limit_apply', parsed_args.task, parsed_args.policy,
                          parsed_args.force)



class Policy_list(Lister):
    """ List available policies """

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        policies = servercmd('limit_list')

        from sets import Set
        resources = Set()
        for name in policies:
            policy = policies[name]
            for resource in policy:
                if resource.lower() == 'monitor':
                    continue
                resources.add(resource.lower())

        columns = ['Name']
        for r in resources:
            columns.append(r)

        columns = tuple(columns)

        values = []
        for name, policy in sorted(policies.iteritems()):
            if name.startswith('__'):
                continue

            v = [name]
            # policy = policies[name]
            for r in resources:
                if policy.get(r, None) is None:
                    l = '-'
                else:
                    l = policy.get(r)
                v.append(l)
            values.append(tuple(v))

        if len(values) == 0:
            columns = ('Policies',)
            values = [('No policies',)]

        return (columns, values)

