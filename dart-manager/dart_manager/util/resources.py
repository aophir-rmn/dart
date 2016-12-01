import logging
import os
from abc import ABCMeta, abstractproperty

from dart_manager import DartManagerError
from dart_manager.ops.stack import DartCore, DartEnv

logger = logging.getLogger(__name__)

class DartResources(object):

    def __init__(self, path):
        self.path = path
        self.core = self._get_resource(DartCore, 'core.yaml')
        self.envs = self._get_resource_group(DartEnv, 'envs')

    def _get_resource(self, ResourceClass, *paths):
        resource_path = os.path.join(self.path, *paths)
        return ResourceClass(resource_path)

    def _get_resource_group(self, ResourceClass, group_name):
        """Get a mapping of resource names to resources in this group"""
        group_path = os.path.join(self.path, group_name)

        if not os.path.exists(group_path):
            logger.verbose('Creating missing "{}" subdirectory in dart-resources'.format(dir_name))
            os.mkdir(group_path)
        elif not os.path.isdir(group_path):
            raise DartManagerError('"{}" exists in Dart resources but is not a directory'.format(dir_name))

        group = {}
        item_names = os.path.listdir(group_path)
        for item_name in item_names:
            resource = self._get_resource(ResourceClass, group_name, item_name)

            if resource.name in group:
                message = 'Duplicate definitions for "{name}" {resource_type}:\n{path1}\n{path2}'
                raise DartManagerError(message.format(
                    name=resource.name,
                    resource_type=self.resource_class.get_resource_type(),
                    path1=resource.path,
                    path2=self[resource.name].path,
                ))

            group[resource.name] = resource


class DartResource(object):
    __metaclass__ = ABCMeta

    resource_type = abstractproperty()
    file_type = abstractproperty()

    def __init__(self, path):
        self.path = path

        basename = os.path.basename(self.path)
        if not basename.endswith(self.file_type):
            raise DartManagerError()  # todo

        self.name = basename[:-len(self.file_type)]


def _disk_op(operation_type):
    def op_decorator(func):
        def wrapper(self):
            try:
                with open(self.path) as file:
                    return func(self, file)
            except Exception as e:
                message = 'Error {op}ing "{name}" {resource_type} from disk:\n{error}'
                raise DartManagerError(message.format(
                    op=operation_type,
                    resource_type=self.name,
                    error=e.message
                ))

        return wrapper
    return op_decorator


load_op = _disk_op('load')
save_op = _disk_op('save')
