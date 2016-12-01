INVALIDATE METADATA;

SET COMPRESSION_CODEC={compression};

INSERT INTO TABLE {destination_table_name}
{partitions}
SELECT *
FROM {source_table_name};
