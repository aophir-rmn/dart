from abc import abstractmethod
import logging
import logging.config
import os
from dart.config.config import configuration, set_dart_environment_variables
from dart.context.context import AppContext


class Tool(object):
    def __init__(self, logger, configure_app_context=True):
        config_path = os.getenv('DART_CONFIG')
        if config_path:
            self.dart_config = configuration(config_path)
            logging.config.dictConfig(self.dart_config['logging'])
            set_dart_environment_variables(self.dart_config['dart'].get('ecs_agent_data_path'))
            logger.info('loaded config from path: %s' % config_path)
            if configure_app_context:
                self.app_context = AppContext(self.dart_config, ['dart.web'])
        else:
            logger.error("missing DART_CONFIG env variable")
            raise ValueError("missing DART_CONFIG env variable")

    @abstractmethod
    def run(self):
        raise NotImplementedError
