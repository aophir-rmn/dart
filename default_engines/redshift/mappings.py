from dart.model.dataset import DataType


column_type_map = {
    DataType.STRING: lambda column: 'VARCHAR(%s)' % (column.length or 'MAX'),
    DataType.VARCHAR: lambda column: 'VARCHAR(%s)' % (column.length or 'MAX'),
    DataType.BIGINT: lambda column: 'BIGINT',
    DataType.INT: lambda column: 'INT',
    DataType.SMALLINT: lambda column: 'SMALLINT',
    DataType.DOUBLE: lambda column: 'DOUBLE',
    DataType.FLOAT: lambda column: 'FLOAT',
    DataType.NUMERIC: lambda column: 'DECIMAL(%s, %s)' % (column.precision, column.scale),
    DataType.BOOLEAN: lambda column: 'BOOLEAN',
    DataType.DATE: lambda column: 'DATE',
    DataType.DATETIME: lambda column: 'TIMESTAMP',
    DataType.TIMESTAMP: lambda column: 'TIMESTAMP'
}


def mapped_column_definition(column=None):
    """
    :type column: dart.model.dataset.Column
    :rtype: str
    """
    type_function = column_type_map[column.data_type.upper()]
    return '"{name}" {type}{not_null}'.format(
        name=column.name,
        type=type_function(column),
        not_null=' NOT NULL' if not column.is_nullable else '',
    )
