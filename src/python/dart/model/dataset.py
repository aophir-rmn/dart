from dart.model.base import BaseModel, dictable


@dictable
class Dataset(BaseModel):
    def __init__(self, id=None, version_id=None, created=None, updated=None, data=None):
        """
        :type id: str
        :type version_id: int
        :type created: datetime.datetime
        :type updated: datetime.datetime
        :type data: dart.model.dataset.DatasetData
        """
        self.id = id
        self.version_id = version_id
        self.created = created
        self.updated = updated
        self.data = data


class Compression(object):
    NONE = 'NONE'
    BZ2 = 'BZ2'
    GZIP = 'GZIP'
    SNAPPY = 'SNAPPY'

    @staticmethod
    def all():
        return [Compression.NONE, Compression.BZ2, Compression.GZIP, Compression.SNAPPY]


class LoadType(object):
    INSERT = 'INSERT'
    MERGE = 'MERGE'
    RELOAD_ALL = 'RELOAD_ALL'
    RELOAD_LAST = 'RELOAD_LAST'

    @staticmethod
    def all():
        return [LoadType.INSERT, LoadType.MERGE, LoadType.RELOAD_ALL, LoadType.RELOAD_LAST]


@dictable
class DatasetData(BaseModel):
    def __init__(self, name, table_name, location, load_type, data_format, columns=None, primary_keys=None,
                 merge_keys=None, sort_keys=None, distribution_keys=None, batch_merge_sort_keys=None,
                 compression=Compression.NONE, partitions=None, hive_compatible_partition_folders=False,
                 description=None, tags=None, user_id='anonymous'):
        """
        :type name: str
        :type table_name: str
        :type location: str
        :type load_type: str
        :type data_format: dart.model.dataset.DataFormat
        :type columns: list[dart.model.dataset.Column]
        :type primary_keys: list[str]
        :type merge_keys: list[str]
        :type sort_keys: list[str]
        :type distribution_keys: list[str]
        :type batch_merge_sort_keys: list[str]
        :type compression: str
        :type partitions: list[dart.model.dataset.Column]
        :type hive_compatible_partition_folders: bool
        :type description: str
        :type tags: list[str]
        """
        self.name = name
        self.table_name = table_name
        self.location = location
        self.load_type = load_type
        self.data_format = data_format
        self.columns = columns
        self.primary_keys = primary_keys or []
        self.merge_keys = merge_keys or []
        self.sort_keys = sort_keys or []
        self.distribution_keys = distribution_keys or []
        self.batch_merge_sort_keys = batch_merge_sort_keys or []
        self.compression = compression
        self.partitions = partitions or []
        self.hive_compatible_partition_folders = hive_compatible_partition_folders
        self.description = description
        self.tags = tags or []
        self.user_id = user_id


@dictable
class DataFormat(BaseModel):
    def __init__(self, file_format=None, row_format=None, num_header_rows=0, delimited_by=None, quoted_by=None,
                 escaped_by=None, null_string=None, regex_input=None, regex_output=None):
        """
        :type file_format: str
        :type row_format: str
        :type num_header_rows: int
        :type delimited_by: str
        :type quoted_by: str
        :type escaped_by: str
        :type null_string: str
        :type regex_input: str
        :type regex_output: str
        """
        self.file_format = file_format
        self.row_format = row_format
        self.num_header_rows = num_header_rows
        self.delimited_by = delimited_by
        self.quoted_by = quoted_by
        self.escaped_by = escaped_by
        self.null_string = null_string
        self.regex_input = regex_input
        self.regex_output = regex_output


@dictable
class Column(BaseModel):
    def __init__(self, name, data_type, length=None, precision=None, scale=None, path=None, date_pattern=None,
                 description=None, is_nullable=True):
        """
        :type name: str
        :type data_type: str
        :type length: int
        :type precision: int
        :type scale: int
        :type path: str
        :type date_pattern: str
        :type description: str
        :type is_nullable: bool
        """
        self.name = name
        self.data_type = data_type
        self.length = length
        self.precision = precision
        self.scale = scale
        self.path = path
        self.date_pattern = date_pattern
        self.description = description
        self.is_nullable = is_nullable


class DataType(object):
    STRING = 'STRING'
    VARCHAR = 'VARCHAR'
    BIGINT = 'BIGINT'
    INT = 'INT'
    SMALLINT = 'SMALLINT'
    DOUBLE = 'DOUBLE'
    FLOAT = 'FLOAT'
    NUMERIC = 'NUMERIC'
    BOOLEAN = 'BOOLEAN'
    DATE = 'DATE'
    DATETIME = 'DATETIME'
    TIMESTAMP = 'TIMESTAMP'

    @staticmethod
    def all():
        return [DataType.STRING, DataType.VARCHAR, DataType.BIGINT, DataType.INT, DataType.SMALLINT, DataType.DOUBLE,
                DataType.FLOAT, DataType.NUMERIC, DataType.BOOLEAN, DataType.DATE, DataType.DATETIME,
                DataType.TIMESTAMP]


class FileFormat(object):
    TEXTFILE = 'TEXTFILE'
    RCFILE = 'RCFILE'
    PARQUET = 'PARQUET'

    @staticmethod
    def all():
        return [FileFormat.TEXTFILE, FileFormat.PARQUET, FileFormat.RCFILE]


class RowFormat(object):
    NONE = 'NONE'
    DELIMITED = 'DELIMITED'
    JSON = 'JSON'
    REGEX = 'REGEX'

    @staticmethod
    def all():
        return [RowFormat.DELIMITED, RowFormat.JSON, RowFormat.REGEX, RowFormat.NONE]
