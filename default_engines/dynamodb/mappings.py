from dart.model.dataset import DataType


column_type_map = {
    DataType.STRING: lambda column: 'S',
    DataType.VARCHAR: lambda column: 'S',
    DataType.BIGINT: lambda column: 'N',
    DataType.INT: lambda column: 'N',
    DataType.SMALLINT: lambda column: 'N',
    DataType.DOUBLE: lambda column: 'N',
    DataType.FLOAT: lambda column: 'N',
    DataType.NUMERIC: lambda column: 'N',
    DataType.BOOLEAN: lambda column: 'N',
    DataType.DATE: lambda column: 'S',
    DataType.DATETIME: lambda column: 'S',
    DataType.TIMESTAMP: lambda column: 'S'
}


def mapped_column_type(column):
    """
    :type column: dart.model.dataset.Column
    :rtype: str
    """
    column_function = column_type_map[column.data_type.upper()]
    return column_function(column)
