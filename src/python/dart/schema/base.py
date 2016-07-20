from jsonschema import Draft4Validator
from jsonschema.exceptions import best_match

from dart.model.exception import DartValidationException


def apply_defaults(instance, schema):
    if not schema or not instance:
        return
    for prop, subschema in schema.get('properties', {}).iteritems():
        if subschema and 'default' in subschema and instance.get(prop) is None:
            instance[prop] = subschema['default']
        if prop in instance:
            apply_defaults(instance[prop], subschema)


def default_and_validate(model, schema):
    instance = model.to_dict()
    apply_defaults(instance, schema)
    errors = list(Draft4Validator(schema).iter_errors(instance))
    if len(errors) > 0:
        raise DartValidationException(str(best_match(errors)))
    return model.from_dict(instance)


def base_schema(data_json_schema):
    data_json_schema['properties']['user_id'] = {'type': 'string', 'pattern': '^[a-zA-Z0-9_-]+$', 'maxLength': 64, 'default': 'unknown', 'readonly': True}
    data_json_schema['required'].append('user_id')
    return {
        'type': 'object',
        'properties': {
            'id': {'type': ['string', 'null'], 'readonly': True},
            'version_id': {'type': ['integer', 'null'], 'readonly': True},
            'created': {'type': ['string', 'null'], 'readonly': True},
            'updated': {'type': ['string', 'null'], 'readonly': True},
            'data': data_json_schema,
        },
        'additionalProperties': False,
        'required': ['data']
    }


def email_list_schema():
    return {
        'x-schema-form': {'type': 'tabarray', 'title': "{{ value || 'email ' + $index }}"},
        'type': 'array',
        'default': [],
        'items': {'type': 'string', 'pattern': '^\\S+@\\S+$'},
        'minItems': 0,
    }


def tag_list_schema():
    return {
        'x-schema-form': {'type': 'tabarray', 'title': "{{ value || 'tag ' + $index }}"},
        'type': 'array',
        'default': [],
        'items': {'type': 'string', 'pattern': '^[a-zA-Z0-9_]+$', 'maxLength': 30},
        'minItems': 0,
    }
