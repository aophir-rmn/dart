import yaml



class ResourceManagementOperation(object):

    _operation = None

    def __init__(self, config, envs, commit):
        self.config = config
        self.envs = envs
        self.commit = commit

    def run(self, operation_class, *args, **kwargs):
        operation = operation_class(self.config, self.envs, self.commit)
        operation.run(*args, **kwargs)


def load_config_file(path):
    with open(path) as f:
        return yaml.load(f)





