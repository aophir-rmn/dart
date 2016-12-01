import logging
from abc import ABCMeta, abstractproperty
from functools import partial

import ruamel.yaml as ryaml
from dart_manager import DartManagerError
from dart_manager.ops.resources import DartResource, load_op, save_op
from dart_manager.util.util import classproperty

logger = logging.getLogger(__name__)


class DartStack(DartResource):
    __metaclass__ = ABCMeta

    stack_type = abstractproperty()

    @classproperty
    def resource_type(cls):
        return '{} stack'.format(cls.stack_type)

    file_type = 'yaml'

    def __init__(self, path):
        super(DartStack, self).__init__(path)

        # lazy loading
        self._spec = None

        self.stack_arn = self._create_spec_property('StackArn')
        self.parameters = self._create_spec_property('Parameters')

    @property
    def spec(self):
        if self._spec is None:
            self._spec = self._load_spec()

        return self._spec

    @load_op
    def _load_spec(self, f):
        return ryaml.round_trip_load(f)

    @save_op
    def save_spec(self, f):
        ryaml.round_trip_dump(self.spec, f)

    def _create_spec_property(self, key):
        if key not in self.spec:
            message = 'Top-level key "{key}" not found in "{stack_name}" {resource_type}'
            raise DartManagerError(message.format(
                key=key,
                stack_name=self.name,
                resource_type=self.resource_type,
            ))

        return property(
            partial(self.spec.__getitem__, key),
            partial(self.spec.__setitem__, key),
        )


class DartCore(DartStack):
    stack_type = 'core'


class DartEnv(DartStack):
    stack_type = 'env'
