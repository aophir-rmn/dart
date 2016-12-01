import os
import shutil
import unittest

from dart.model.dataset import Dataset, DatasetData, DataFormat, Column, FileFormat, RowFormat
from dart.util.shell import call

from engine.emr import hive_copy_to_table


class TestHiveTransformJsonToTableStep(unittest.TestCase):

    def test_hive_table_definition_step(self):
        ds = Dataset(data=DatasetData(
            name='weblogs_v01',
            table_name='weblogs',
            location='s3://wsm-log-servers/weblogs/www.retailmenot.com/ec2/',
            data_format=DataFormat(
                file_format=FileFormat.TEXTFILE,
                row_format=RowFormat.REGEX,
                regex_input="(?<ip>^(?:(?:unknown(?:,\\s)?|(?:\\d+\\.\\d+\\.\\d+\\.\\d+(?:,\\s)?))+)|\\S*)\\s+\\S+\\s+(?<userIdentifier>(?:[^\\[]+|\\$\\S+\\['\\S+'\\]|\\[username\\]))\\s*\\s+\\[(?<requestDate>[^\\]]+)\\]\\s+\"(?<httpMethod>(?:GET|HEAD|POST|PUT|DELETE|TRACE))\\s(?<urlPath>(?:[^ ?]+))(?:\\?(?<queryString>(?:[^ ]+)))?\\sHTTP/(?<httpVersion>(?:[\\d\\.]+))\"\\s+(?<statusCode>[0-9]+)\\s+(?<bytesSent>\\S+)\\s+\"(?<referrer>(?:[^\"\\\\]*(?:\\\\.[^\"\\\\]*)*))\"\\s+\"(?<userAgent>(?:[^\"\\\\]*(?:\\\\.[^\"\\\\]*)*))\"\\s+(?<responseTime>[-0-9]*)\\s+\"(?<hostName>(?:[^\"\\\\]*(?:\\\\.[^\"\\\\]*)*))\"\\s+\"(?<userFingerprint>(?:[^\"\\\\]*(?:\\\\.[^\"\\\\]*)*))\"\\s+\"(?<userId>(?:[^\"\\\\]*(?:\\\\.[^\"\\\\]*)*))\"\\s+\"(?<sessionId>(?:[^\"\\\\]*(?:\\\\.[^\"\\\\]*)*))\"\\s+\"(?<requestId>(?:[^\"\\\\]*(?:\\\\.[^\"\\\\]*)*))\"\\s+\"(?<visitorId>(?:[^\"\\\\]*(?:\\\\.[^\"\\\\]*)*))\"\\s+\"(?<vegSlice>(?:[^\"\\\\]*(?:\\\\.[^\"\\\\]*)*))\"\\s+\"(?<fruitSlice>(?:[^\"\\\\]*(?:\\\\.[^\"\\\\]*)*))\"\\s+\"(?<cacheHitMiss>(?:[^\"\\\\]*(?:\\\\.[^\"\\\\]*)*))\"\\s*\\Z",
                regex_output="%1$s %2$s %3$s %4$s %5$s %6$s %7$s %8$s %9$s %10$s %11$s %12$s %13$s %14$s %15$s %16$s %17$s %18$s %19$s %20$s %21s",
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

        call('mkdir -p /tmp/dart-emr-test/hive/')
        this_path = os.path.dirname(os.path.abspath(__file__))
        shutil.copyfile(this_path + '/../../../engine/emr/steps/hive/copy_to_table.hql', '/tmp/dart-emr-test/hive/copy_to_table.hql')
        hive_copy_to_table(ds, 'weblogs_stage', ds, 'weblogs', 's3://test', '/tmp/dart-emr-test/', 'actionid123', None, 1, 1)

        with open(os.path.join(this_path, 'copy_to_table_weblogs.hql')) as f:
            expected_contents = f.read()

        with open('/tmp/dart-emr-test/hive/copy_to_table_weblogs.hql') as f:
            actual_contents = f.read()

        self.assertEqual(expected_contents, actual_contents)

if __name__ == '__main__':
    unittest.main()
