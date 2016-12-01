import os
import unittest
import shutil
from engine.emr import hive_copy_to_table

from dart.model.dataset import Dataset, DatasetData, DataFormat, Column, FileFormat, RowFormat, DataType
from dart.util.shell import call


class TestHiveTransformJsonToTableStep(unittest.TestCase):

    def test_hive_table_definition_step(self):
        ds = Dataset(data=DatasetData(
            name='owen_eu_v01',
            table_name='owen_eu',
            location='s3://s3-rpt-uss-dat-warehouse/prd/inbound/overlord/eu-all-events',
            data_format=DataFormat(
                file_format=FileFormat.TEXTFILE,
                row_format=RowFormat.JSON,
            ),
            columns=[
                Column('host', 'STRING', path='metadata.host'),
                Column('pageName', 'STRING', path='owen.context.pageName'),
                Column('viewInstanceUuid', 'STRING', path='owen.context.viewInstanceUuid'),
                Column('previousPageName', 'STRING', path='owen.context.previousPageName'),
                Column('previousViewInstanceUuid', 'STRING', path='owen.context.previousViewInstanceUuid'),
                Column('session', 'STRING', path='owen.context.session'),
                Column('pageType', 'STRING', path='owen.context.pageType'),
                Column('propertyName', 'STRING', path='owen.context.propertyName'),
                Column('enviroment', 'STRING', path='owen.context.environment'),
                Column('appForegroundFlag', 'BOOLEAN', path='owen.context.appForegroundFlag'),
                Column('bluetoothEnabledFlag', 'BOOLEAN', path='owen.context.bluetoothEnabledFlag'),
                Column('favoriteFlag', 'BOOLEAN', path='owen.context.favoriteFlag'),
                Column('locationEnabledFlag', 'BOOLEAN', path='owen.context.locationEnabledFlag'),
                Column('loggedInFlag', 'BOOLEAN', path='owen.context.loggedInFlag'),
                Column('notificationEnabledFlag', 'BOOLEAN', path='owen.context.notificationEnabledFlag'),
                Column('personalizationFlag', 'BOOLEAN', path='owen.context.personalizationFlag'),
                Column('advertiserUuid', 'STRING', path='owen.context.advertiserUuid'),
                Column('udid', 'STRING', path='owen.context.udid'),
                Column('userQualifier', 'STRING', path='owen.context.userQualifier'),
                Column('userId', 'STRING', path='owen.context.custom.legacy.userId'),
                Column('userUuid', 'STRING', path='owen.context.userUuid'),
                Column('macAddress', 'STRING', path='owen.context.macAddress'),
                Column('ipAddress', 'STRING', path='owen.context.ipAddress'),
                Column('osVersion', 'STRING', path='owen.context.osVersion'),
                Column('osFamily', 'STRING', path='owen.context.osFamily'),
                Column('osName', 'STRING', path='owen.context.osName'),
                Column('browserFamily', 'STRING', path='owen.context.browserFamily'),
                Column('deviceCategory', 'STRING', path='owen.context.deviceCategory'),
                Column('deviceMake', 'STRING', path='owen.context.mobileDeviceMake'),
                Column('deviceModel', 'STRING', path='owen.context.mobileDeviceModel'),
                Column('connectionType', 'STRING', path='owen.context.connectionType'),
                Column('userAgent', 'STRING', path='owen.context.userAgent'),
                Column('geofenceId', 'STRING', path='owen.context.custom.legacy.geofenceId'),
                Column('eventTimestamp', 'TIMESTAMP', path='owen.event.eventTimestamp', date_pattern="yyyy-MM-dd'T'HH:mm:ssZ"),
                Column('eventInstanceUuid', 'STRING', path='owen.event.eventInstanceUuid'),
                Column('eventPlatformVersion', 'STRING', path='owen.event.eventPlatformVersion'),
                Column('eventVersion', 'STRING', path='owen.event.eventVersion'),
                Column('eventCategory', 'STRING', path='owen.event.eventCategory'),
                Column('eventName', 'STRING', path='owen.event.eventName'),
                Column('eventAction', 'STRING', path='owen.event.eventAction'),
                Column('eventPlatform', 'STRING', path='owen.event.eventPlatform'),
                Column('testUnixTimestampSecondsPattern', 'TIMESTAMP', path='some.fake.path.testUnixTimestampSecondsPattern', date_pattern='UNIX_TIMESTAMP_SECONDS'),
                Column('testUnixTimestampMillisPattern', 'TIMESTAMP', path='some.fake.path.testUnixTimestampMillisPattern', date_pattern='UNIX_TIMESTAMP_MILLIS'),
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
        action_id = 'actionid123'

        target_dataset = Dataset.from_dict(ds.to_dict())
        target_dataset.data.data_format.num_header_rows = 0
        target_dataset.data.data_format = DataFormat(FileFormat.RCFILE, RowFormat.NONE)
        stage_dataset = Dataset.from_dict(ds.to_dict())
        assert isinstance(stage_dataset, Dataset)
        for c in stage_dataset.data.columns:
            c.data_type = DataType.STRING

        hive_copy_to_table(stage_dataset, 'owen_eu_stage', target_dataset, 'owen_eu', 's3://test', '/tmp/dart-emr-test/', action_id, None, 1, 1)

        with open(os.path.join(this_path, 'copy_to_table_owen_eu.hql')) as f:
            expected_contents = f.read()

        with open('/tmp/dart-emr-test/hive/copy_to_table_owen_eu.hql') as f:
            actual_contents = f.read()

        self.assertEqual(expected_contents, actual_contents)

if __name__ == '__main__':
    unittest.main()
