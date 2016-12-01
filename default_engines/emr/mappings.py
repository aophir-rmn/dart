from dart.model.dataset import DataType


column_type_map = {
    DataType.STRING: lambda column: 'STRING',
    DataType.VARCHAR: lambda column: 'STRING',
    DataType.BIGINT: lambda column: 'BIGINT',
    DataType.INT: lambda column: 'INT',
    DataType.SMALLINT: lambda column: 'INT',
    DataType.DOUBLE: lambda column: 'DOUBLE',
    DataType.FLOAT: lambda column: 'FLOAT',
    DataType.NUMERIC: lambda column: 'DECIMAL(%s, %s)' % (column.precision, column.scale),
    DataType.BOOLEAN: lambda column: 'BOOLEAN',
    DataType.DATE: lambda column: 'DATE',
    DataType.DATETIME: lambda column: 'TIMESTAMP',
    DataType.TIMESTAMP: lambda column: 'TIMESTAMP'
}


def mapped_column_type(column):
    """
    :type column: dart.model.dataset.Column
    :rtype: str
    """
    column_function = column_type_map[column.data_type.upper()]
    return column_function(column)


def dynamodb_column_type(column):
    mapped_type = mapped_column_type(column)
    if mapped_type in ['STRING', 'DATE', 'TIMESTAMP']:
        return 'STRING'
    if mapped_type in ['BIGINT', 'INT', 'BOOLEAN']:
        return 'BIGINT'
    if mapped_type in ['DOUBLE', 'FLOAT'] or mapped_type.startswith('DECIMAL'):
        return 'DOUBLE'
    raise Exception('unsupported mapped_column_type: %s' % mapped_type)


instance_disk_space_map = {
    'm3.2xlarge': 160 * 1000000000L
}
