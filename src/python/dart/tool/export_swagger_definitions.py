#
# Usage:
# - Delete everything following and including "definitions:" from src/swagger/swagger.yaml
# - python src/python/dart/tool/export_swagger_definitions.py >> src/swagger/swagger.yaml
#
import sys
from yaml import dump
try:
    from yaml import CDumper as Dumper
except ImportError:
    from yaml import Dumper

from dart.model.query import Operator, Direction
from dart.schema.action import action_schema
from dart.schema.dataset import columns_schema, dataset_schema
from dart.schema.datastore import datastore_schema
from dart.schema.engine import engine_schema, subgraph_definition_schema
from dart.schema.event import event_schema
from dart.schema.subscription import subscription_schema
from dart.schema.trigger import trigger_schema, trigger_type_schema
from dart.schema.workflow import workflow_schema, workflow_instance_schema


def main():
    data = {
        'definitions': {
            'Action': action_schema(None),
            'ActionContext': action_context_schema(),
            'ActionResult': action_result_schema(),
            'Dataset': dataset_schema(),
            'Datastore': datastore_schema(None),
            'Engine': engine_schema(),
            'ErrorResult': error_result_schema(),
            'Event': event_schema(),
            'Filter': filter_schema(),
            'GraphEntityIdentifier': graph_entity_identifier_schema(),
            'GraphEntity': graph_entity_schema(),
            'JSONPatch': json_patch_schema(),
            'JSONSchema': json_schema_schema(),
            'OKResult': ok_result_schema(),
            'OrderBy': order_by_schema(),
            'SubGraph': sub_graph_schema(),
            'SubGraphDefinition': {'type': 'object'}, #subgraph_definition_schema([{'type': 'object'}], [{'type': 'object'}], {'type': 'object'}),
            'Subscription': subscription_schema(),
            'Trigger': trigger_schema({'type': 'object'}),
            'TriggerType': trigger_type_schema(),
            'Workflow': workflow_schema(),
            'WorkflowInstance': workflow_instance_schema()
        }
    }
    fix_up(data, data, [None])
    print dump(data, Dumper=Dumper, default_style=None, default_flow_style=False, explicit_start=False, explicit_end=False)
    return 0


def action_context_schema():
    return {'type': 'object'}


def action_result_schema():
    return {'type': 'object'}


def error_result_schema():
    return {
        'type': 'object',
        'properties': {
            'results': {
                'type': 'string',
                'enum': ["ERROR"]
            },
            'error_message': {
                'type': 'string'
            }
        }
    }


def filter_schema():
    return {
        'type': 'object',
        'properties': {
            'key': {
                'type': 'string'
            },
            'operator': {
                'type': 'string',
                'enum': [getattr(Operator, attr) for attr in dir(Operator) if not attr.startswith('__')]
            },
            'value': {
                'type': 'string'
            }
        }
    }


def graph_entity_identifier_schema():
    return {
        'type': 'object',
        'properties': {
            'entity_type': {
                'type': 'string'
            },
            'entity_id': {
                'type': 'string'
            },
            'name': {
                'type': 'string'
            },
        }
    }


def graph_entity_schema():
    return {
        'type': 'object',
        'properties': {
            'entity_type': {
                'type': 'string'
            },
            'entity_id': {
                'type': 'string'
            },
            'name': {
                'type': 'string'
            },
            'state': {
                'type': 'string'
            },
            'sub_type': {
                'type': 'string'
            },
            'related_type': {
                'type': 'string'
            },
            'related_id': {
                'type': 'string'
            },
            'related_is_a': {
                'type': 'string'
            },
        }
    }


def json_patch_schema():
    return {
        'type': 'object',
        'description': "JSON Patch object as defined by http://json.schemastore.org/json-patch"
    }


def json_schema_schema():
    return {
        'type': 'object',
        'description': "JSON Schema object as defined by http://json-schema.org/schema"
    }


def ok_result_schema():
    return {
        'type': 'object',
        'properties': {
            'results': {
                'type': 'string',
                'enum': ["OK"]
            }
        }
    }


def order_by_schema():
    return {
        'type': 'object',
        'properties': {
            'key': {
                'type': 'string'
            },
            'direction': {
                'type': 'string',
                'enum': [getattr(Direction, attr) for attr in dir(Direction) if not attr.startswith('__')]
            }
        }
    }


def sub_graph_schema():
    return {'type': 'object'}


def fix_up(data, root, path):
    """
    Fix up the JSON schemas from the dart.schema package and transform them into
    Swagger compatible definitions. Transform any embedded object definitions into
    top level definitions. Remove the use of readonly and placeholder attributes.
    Remove the use of null defaults as they aren't yet fully supported by the
    Open API Specification.

    See https://github.com/OAI/OpenAPI-Specification/issues/229

    :param data: The current dictionary in the traversal
    :param root: The root dictionary
    :param path: A list containing the path to root
    :return:
    """
    parent = path[-1]
    for key, value in data.items():
        if key == 'type':
            if isinstance(value, list):
                try:
                    value.remove('null')
                except ValueError:
                    pass
                data[key] = value[0]
        elif key == 'readonly':
            del data[key]
        elif key == 'placeholder':
            del data[key]
        elif key == 'default' and value is None:
            del data[key]
        elif key in ['columns', 'partitions', 'supported_action_types'] and parent == 'properties':
            if key in ['columns', 'partitions']:
                schema = 'Column'
            elif key == 'supported_action_types':
                schema = 'ActionType'
            items = value['items']
            value['items'] = {
                '$ref': ('#/definitions/%s' % schema)
            }
            if schema not in root['definitions']:
                root['definitions'][schema] = items
                fix_up(items, root, ['definitions', schema])
        elif key in ['data', 'data_format'] and parent == 'properties':
            if key == 'data':
                schema = '%sData' % path[2]
            elif key == 'data_format':
                schema = 'DataFormat'
            data[key] = {
                '$ref': ('#/definitions/%s' % schema)
            }
            root['definitions'][schema] = value
            fix_up(value, root, ['definitions', schema])
        elif isinstance(value, dict):
            path.append(key)
            fix_up(value, root, path)
            path.pop()


if __name__ == '__main__':
    sys.exit(main())
