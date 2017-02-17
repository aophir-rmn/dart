""" These methods allow access to dart.yaml config file values. """

import os
import logging
from dart.config.config import configuration

_logger = logging.getLogger(__name__)
config_path = os.environ['DART_CONFIG']
config = configuration(config_path)


def get_key(key_path):
    """ get_key if yaml[key_path[0]][key_path[1]]... exists. E.g.
        get_key( ['dart'] ) ={...}
        get_key( ['dart', 'env_name']) = "local"
        get_key( ['env_name', 'dart']) == None
    """
    current = config
    for key in key_path:
        if key in current:
            current = current[key]
        else:
            return None

    return current

def does_key_exist(key_path):
    return get_key(key_path) != None