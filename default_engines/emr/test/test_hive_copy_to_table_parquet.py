import os
import shutil
import unittest

from dart.model.dataset import Dataset, DatasetData, DataFormat, Column, FileFormat, RowFormat
from dart.util.shell import call

from engine.emr import impala_copy_to_table


class TestHiveTransformJsonToTableStep(unittest.TestCase):

    def test_impala_table_definition_step(self):
        ds = Dataset(data=DatasetData(
            name='weblogs_v01',
            table_name='weblogs_parquet',
            location='s3://wsm-log-servers/weblogs/www.retailmenot.com/ec2/',
            data_format=DataFormat(
                file_format=FileFormat.PARQUET,
                row_format=RowFormat.NONE,
            ),
            columns=[
                Column('ip', 'STRING'),
                Column('user', 'STRING'),
                Column('requestDate', 'TIMESTAMP', date_pattern='dd/MMM/yyyy:HH:mm:ss Z'),
                Column('httpMethod', 'STRING'),
                Column('urlPath', 'STRING'),
                Column('queryString', 'STRING'),
                Column('httpVersion', 'STRING'),
                Column('statusCode', 'STRING'),
                Column('bytesSent', 'INT'),
                Column('referrer', 'STRING'),
                Column('userAgent', 'STRING'),
                Column('responseTime', 'BIGINT'),
                Column('hostname', 'STRING'),
                Column('userFingerprint', 'STRING'),
                Column('userId', 'STRING'),
                Column('sessionId', 'STRING'),
                Column('requestId', 'STRING'),
                Column('visitorId', 'STRING'),
                Column('vegSlice', 'STRING'),
                Column('fruitSlice', 'STRING'),
                Column('cacheHitMiss', 'STRING'),
            ],
            compression='GZIP',
            partitions=[
                Column('year', 'STRING'),
                Column('week', 'STRING'),
                Column('day', 'STRING'),
            ],
        ))

        call('mkdir -p /tmp/dart-emr-test/impala/')
        this_path = os.path.dirname(os.path.abspath(__file__))
        shutil.copyfile(this_path + '/../../../engine/emr/steps/impala/copy_to_table.sql', '/tmp/dart-emr-test/impala/copy_to_table.sql')
        impala_copy_to_table(ds, 'weblogs_stage', ds, 'weblogs_parquet', 's3://test', '/tmp/dart-emr-test/', 'actionid123', 1, 1)

        with open(os.path.join(this_path, 'copy_to_table_weblogs_parquet.sql')) as f:
            expected_contents = f.read()

        with open('/tmp/dart-emr-test/impala/copy_to_table_weblogs_parquet.sql') as f:
            actual_contents = f.read()

        self.assertEqual(expected_contents, actual_contents)

if __name__ == '__main__':
    unittest.main()
