import re
from datetime import timedelta

first_cap_re = re.compile('(.)([A-Z][a-z]+)')
all_cap_re = re.compile('([a-z0-9])([A-Z])')


# values = ["09:59:59", "1 days, 11:54:33", "-12 days, 00:02:11"]
# for value in values:
#      match = timedelta_re.match(value).groupdict()
#      print (match)
# Returns:
# {'hours': '09', 'seconds': '59', 'minutes': '59', 'days': None}
# {'hours': '11', 'seconds': '33', 'minutes': '54', 'days': '1'}
# {'hours': '00', 'seconds': '11', 'minutes': '02', 'days': '-12'}
timedelta_re = re.compile(r'((?P<days>[\-]?[0-9]{1,3}) days?, )?(?P<hours>[0-9]{1,2}):(?P<minutes>[0-9]{2}):(?P<seconds>[0-9]{2})')

# http://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-camelcase-to-camel-case
def to_snake_case(name):
    s1 = first_cap_re.sub(r'\1_\2', name)
    return all_cap_re.sub(r'\1_\2', s1).lower()


def substitute_date_tokens(s, dt, date_offset_in_seconds=0):
    if not s:
        return s
    if date_offset_in_seconds:
        dt = dt + timedelta(seconds=date_offset_in_seconds)
    return s.replace(
        '{YEAR}', dt.strftime('%Y')).replace(
        '{MONTH}', dt.strftime('%m')).replace(
        '{DAY}', dt.strftime('%d')).replace(
        '{HOUR}', dt.strftime('%H')).replace(
        '{MINUTE}', dt.strftime('%M')).replace(
        '{SECOND}', dt.strftime('%S'))
