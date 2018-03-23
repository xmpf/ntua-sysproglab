import logging
from cliff.lister import Lister
import jsonrpclib


class Resource_list(Lister):
    """ List available resources """

    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        jsonrpclib.config.version = 1.0
        server = jsonrpclib.Server('http://localhost:8080')

        return (tuple(['Resource']), [tuple([r]) for r in server.resource_list()])
