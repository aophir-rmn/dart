import inspect
from itertools import izip_longest
from pydoc import locate
import re
import datetime
import dateutil.parser

from dart.util.strings import timedelta_re


class BaseModel(object):
    def to_dict(self):
        # implemented at runtime by @dictable
        pass

    @classmethod
    def from_dict(cls, dict_obj):
        # implemented at runtime by @dictable
        pass

    def copy(self):
        return self.from_dict(self.to_dict())

    def __str__(self):
        sb = []
        for key in self.__dict__:
            sb.append("{key}='{value}'".format(key=key, value=self.__dict__[key]))

        return ', '.join(sb)

    def __repr__(self):
        return self.__str__()

def to_dict(value):
    if isinstance(value, datetime.datetime):
        return value.isoformat()
    if isinstance(value, datetime.timedelta):
        return str(value).split('.')[0] if value.microseconds else str(value)
    if isinstance(value, datetime.date):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: to_dict(v) for k, v in value.iteritems()}
    if isinstance(value, list):
        return [to_dict(v) for v in value]
    if hasattr(value, '__dictable_public_fields_with_defaults'):
        return {field: to_dict(getattr(value, field)) for field in vars(value)}
    return value


def from_dict(cls, dict_obj):
    args = {}
    for field, default in cls.__dictable_public_fields_with_defaults:
        field_typestr = cls.__dictable_public_field_typestr_by_name.get(field)
        value = decode_from_dict(field_typestr, dict_obj.get(field, default))
        args[field] = value
    return cls(**args)


def decode_from_dict(field_typestr, value):
    if not value or not field_typestr:
        return value

    if field_typestr == 'datetime.datetime':
        return dateutil.parser.parse(value)
    if field_typestr == 'datetime.timedelta':
        match = timedelta_re.match(value).groupdict()
        for k, v in match.items():
            match[k] = int(v) if v is not None else 0
        return datetime.timedelta(**match)
    if field_typestr == 'datetime.date':
        return dateutil.parser.parse(value).date()
    if field_typestr.startswith('dict'):
        if field_typestr == 'dict':
            return value
        # ensure sensible keys
        assert field_typestr[:9] == 'dict[str,'
        dict_value_typestr = field_typestr[9:-1]
        return {k: decode_from_dict(dict_value_typestr, v) for k, v in value.iteritems()}

    if field_typestr.startswith('list'):
        list_typestr = field_typestr[5:-1]
        return [decode_from_dict(list_typestr, v) for v in value]

    cls = locate(field_typestr)
    if hasattr(cls, '__dictable_public_fields_with_defaults'):
        return from_dict(cls, value)

    return cls(value)


def dictable(cls):
    doc_string_lines = [l.strip() for l in cls.__init__.__doc__.split('\n')]
    type_lines = [l for l in doc_string_lines if l.startswith(':type')]

    # example:
    # :type host: str
    type_line_pattern = re.compile(r':type\s+(\S+)\s*:\s*(\S+)')
    cls.__dictable_public_field_typestr_by_name = {}
    for line in type_lines:
        m = type_line_pattern.match(line)
        cls.__dictable_public_field_typestr_by_name[m.group(1)] = m.group(2).replace(' ', '')

    arg_names, vargs, kwargs, defaults = inspect.getargspec(cls.__init__)
    assert vargs is None
    assert kwargs is None

    cls.__dictable_public_fields_with_defaults = list(izip_longest(reversed(arg_names[1:]), reversed(defaults or [])))
    cls.to_dict = lambda self: to_dict(self)
    cls.from_dict = classmethod(lambda clz, dict_obj: from_dict(clz, dict_obj))

    return cls
