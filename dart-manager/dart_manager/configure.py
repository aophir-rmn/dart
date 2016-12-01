import click
import yaml
from dart_manager.cli import dart_manager
from pkg_resources import resource_filename


class DartManagerConfig(dict):
    _PATH = resource_filename(__name__, 'config.yaml')

    # config keys
    RESOURCES = 'dart_resources'

    def __init__(self):
        super(DartManagerConfig, self).__init__()

        with open(self._PATH) as f:
            config = yaml.load(f)

        if isinstance(config, dict):
            self.update(config)

    def save(self):
        with open(self._PATH, 'w') as f:
            return yaml.dump(self, f)


