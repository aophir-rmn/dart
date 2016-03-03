from dart.client.python.dart_client import Dart
from dart.model.dataset import Column, DatasetData, Dataset, DataFormat, FileFormat, RowFormat, DataType, Compression, \
    LoadType

if __name__ == '__main__':
    dart = Dart('localhost', 5000)
    assert isinstance(dart, Dart)

    dataset = dart.save_dataset(Dataset(data=(DatasetData(
        name='owen_outclick_us_v02',
        description='Owen outclick data, based on overlord schema version. Considered a replacement for outclick events.',
        table_name='outclick',
        location='s3://example-bucket/prd/inbound/overlord/raw-firehose-02/rmn-outclicks',
        load_type=LoadType.MERGE,
        data_format=DataFormat(
            file_format=FileFormat.TEXTFILE,
            row_format=RowFormat.JSON,
        ),
        compression=Compression.GZIP,
        partitions=[
            Column('year', DataType.STRING),
            Column('month', DataType.STRING),
            Column('day', DataType.STRING),
        ],
        primary_keys=['eventInstanceUuid'],
        merge_keys=['eventInstanceUuid'],
        sort_keys=['eventTimestamp', 'eventInstanceUuid', 'derivedEventInstanceId'],
        distribution_keys=['eventInstanceUuid'],
        batch_merge_sort_keys=['owenProcessed DESC'],
        columns=[
            Column('advertiserUuid', DataType.VARCHAR, length=2048, path='owen.context.advertiserUuid'),
            Column('appBadgeCount', DataType.INT, path='owen.context.appBadgeCount'),
            Column('appForegroundFlag', DataType.BOOLEAN, path='owen.context.appForegroundFlag'),
            Column('bluetoothBeaconId', DataType.VARCHAR, length=50, path='owen.context.bluetoothBeaconId'),
            Column('bluetoothBeaconType', DataType.VARCHAR, length=25, path='owen.context.bluetoothBeaconType'),
            Column('bluetoothEnabledFlag', DataType.BOOLEAN, path='owen.context.bluetoothEnabledFlag'),
            Column('breadCrumb', DataType.VARCHAR, length=2048, path='owen.context.breadCrumb'),
            Column('browserFamily', DataType.VARCHAR, length=50, path='owen.context.browserFamily'),
            Column('browserVersion', DataType.VARCHAR, length=50, path='owen.context.browserVersion'),
            Column('carrier', DataType.VARCHAR, length=25, path='owen.context.carrier'),
            Column('city', DataType.VARCHAR, length=75, path='owen.context.city'),
            Column('connectionType', DataType.VARCHAR, length=25, path='owen.context.connectionType'),
            Column('country', DataType.VARCHAR, length=2, path='owen.context.country'),
            Column('custom', DataType.VARCHAR, path='owen.context.custom'),
            Column('deviceCategory', DataType.VARCHAR, length=2048, path='owen.context.deviceCategory'),
            Column('deviceFingerprint', DataType.VARCHAR, length=26, path='owen.context.deviceFingerprint'),
            Column('dma', DataType.INT, path='owen.context.dma'),
            Column('environment', DataType.VARCHAR, length=2048, path='owen.context.environment'),
            Column('experimentObject', DataType.VARCHAR, length=1024, path='owen.context.experiment'),
            Column('failureFlag', DataType.BOOLEAN, path='owen.context.failureFlag'),
            Column('failureReason', DataType.VARCHAR, length=2048, path='owen.context.failureReason'),
            Column('favoriteFlag', DataType.BOOLEAN, path='owen.context.favoriteFlag'),
            Column('featureFlags', DataType.VARCHAR, path='owen.context.featureFlags'),
            Column('geofenceUuid', DataType.VARCHAR, length=2048, path='owen.context.geofenceUuid'),
            Column('inventoryCount', DataType.INT, path='owen.context.inventoryCount'),
            Column('inventory_affiliateNetwork', DataType.VARCHAR, length=50, path='owen.context.inventory[0].affiliateNetwork'),
            Column('inventory_brand', DataType.VARCHAR, length=100, path='owen.context.inventory[0].brand'),
            Column('inventory_claimUuid', DataType.VARCHAR, length=2048, path='owen.context.inventory[0].claimUuid'),
            Column('inventory_clickLocation', DataType.VARCHAR, length=100, path='owen.context.inventory[0].clickLocation'),
            Column('inventory_commentsCount', DataType.INT, path='owen.context.inventory[0].commentsCount'),
            Column('inventory_conquestingFlag', DataType.BOOLEAN, path='owen.context.inventory[0].conquestingFlag'),
            Column('inventory_couponRank', DataType.NUMERIC, precision=18, scale=4, path='owen.context.inventory[0].couponRank'),
            Column('inventory_deepLinkUrl', DataType.VARCHAR, length=2048, path='owen.context.inventory[0].deepLinkUrl'),
            Column('inventory_deepLinkUrlScheme', DataType.VARCHAR, length=2048, path='owen.context.inventory[0].deepLinkUrlScheme'),
            Column('inventory_exclusivityFlag', DataType.BOOLEAN, path='owen.context.inventory[0].exclusivityFlag'),
            Column('inventory_expirationDate', DataType.VARCHAR, length=2048, path='owen.context.inventory[0].expirationDate'),
            Column('inventory_finalPrice', DataType.NUMERIC, precision=18, scale=4, path='owen.context.inventory[0].finalPrice'),
            Column('inventory_instoreType', DataType.VARCHAR, length=2048, path='owen.context.inventory[0].instoreType'),
            Column('inventory_inventoryChannel', DataType.VARCHAR, length=2048, path='owen.context.inventory[0].inventoryChannel'),
            Column('inventory_inventoryName', DataType.VARCHAR, length=2048, path='owen.context.inventory[0].inventoryName'),
            Column('inventory_inventorySource', DataType.VARCHAR, length=50, path='owen.context.inventory[0].inventorySource'),
            Column('inventory_inventoryType', DataType.VARCHAR, length=25, path='owen.context.inventory[0].inventoryType'),
            Column('inventory_inventoryUuid', DataType.VARCHAR, length=2048, path='owen.context.inventory[0].inventoryUuid'),
            Column('inventory_lastVerifiedDate', DataType.VARCHAR, length=2048, path='owen.context.inventory[0].lastVerifiedDate'),
            Column('inventory_monetizableFlag', DataType.BOOLEAN, path='owen.context.inventory[0].monetizableFlag'),
            Column('inventory_noVotes', DataType.INT, path='owen.context.inventory[0].noVotes'),
            Column('inventory_onlineType', DataType.VARCHAR, length=2048, path='owen.context.inventory[0].onlineType'),
            Column('inventory_originalPrice', DataType.NUMERIC, precision=18, scale=4, path='owen.context.inventory[0].originalPrice'),
            Column('inventory_outRedirectUrl', DataType.VARCHAR, length=2048, path='owen.context.inventory[0].outRedirectUrl'),
            Column('inventory_outclickUuid', DataType.VARCHAR, length=2048, path='owen.context.inventory[0].outclickUuid'),
            Column('inventory_parentInventoryUuid', DataType.VARCHAR, length=2048, path='owen.context.inventory[0].parentInventoryUuid'),
            Column('inventory_personalizationFlag', DataType.BOOLEAN, path='owen.context.inventory[0].personalizationFlag'),
            Column('inventory_position', DataType.INT, path='owen.context.inventory[0].position'),
            Column('inventory_proximity', DataType.NUMERIC, precision=18, scale=4, path='owen.context.inventory[0].proximity'),
            Column('inventory_proximityUnit', DataType.VARCHAR, length=2048, path='owen.context.inventory[0].proximityUnit'),
            Column('inventory_recommendedFlag', DataType.BOOLEAN, path='owen.context.inventory[0].recommendedFlag'),
            Column('inventory_redemptionChannel', DataType.VARCHAR, length=2048, path='owen.context.inventory[0].redemptionChannel'),
            Column('inventory_retailCategory', DataType.VARCHAR, length=75, path='owen.context.inventory[0].retailCategory'),
            Column('inventory_savedFlag', DataType.BOOLEAN, path='owen.context.inventory[0].savedFlag'),
            Column('inventory_siteUuid', DataType.VARCHAR, length=26, path='owen.context.inventory[0].siteUuid'),
            Column('inventory_startDate', DataType.VARCHAR, length=2048, path='owen.context.inventory[0].startDate'),
            Column('inventory_successPercentage', DataType.NUMERIC, precision=18, scale=4, path='owen.context.inventory[0].successPercentage'),
            Column('inventory_usedByCount', DataType.INT, path='owen.context.inventory[0].usedByCount'),
            Column('inventory_yesVotes', DataType.INT, path='owen.context.inventory[0].yesVotes'),
            Column('ipAddress', DataType.VARCHAR, length=45, path='owen.context.ipAddress'),
            Column('language', DataType.VARCHAR, length=6, path='owen.context.language'),
            Column('latitude', DataType.NUMERIC, precision=18, scale=4, path='owen.context.latitude'),
            Column('locationEnabledFlag', DataType.BOOLEAN, path='owen.context.locationEnabledFlag'),
            Column('loggedInFlag', DataType.BOOLEAN, path='owen.context.loggedInFlag'),
            Column('longitude', DataType.NUMERIC, precision=18, scale=4, path='owen.context.longitude'),
            Column('macAddress', DataType.VARCHAR, length=2048, path='owen.context.macAddress'),
            Column('marketing_adGroup', DataType.VARCHAR, length=2048, path='owen.context.marketing.adGroup'),
            Column('marketing_campaign', DataType.VARCHAR, length=50, path='owen.context.marketing.campaign'),
            Column('marketing_campaignSendCount', DataType.INT, path='owen.context.marketing.campaignSendCount'),
            Column('marketing_campaignUuid', DataType.VARCHAR, length=2048, path='owen.context.marketing.campaignUuid'),
            Column('marketing_cdRank', DataType.INT, path='owen.context.marketing.cdRank'),
            Column('marketing_channel', DataType.VARCHAR, length=50, path='owen.context.marketing.channel'),
            Column('marketing_content', DataType.VARCHAR, length=2048, path='owen.context.marketing.content'),
            Column('marketing_medium', DataType.VARCHAR, length=50, path='owen.context.marketing.medium'),
            Column('marketing_notificationUuid', DataType.VARCHAR, length=2048, path='owen.context.marketing.notificationUuid'),
            Column('marketing_source', DataType.VARCHAR, length=100, path='owen.context.marketing.source'),
            Column('marketing_term', DataType.VARCHAR, length=2048, path='owen.context.marketing.term'),
            Column('marketing_vendor', DataType.VARCHAR, length=25, path='owen.context.marketing.vendor'),
            Column('mobileDeviceMake', DataType.VARCHAR, length=25, path='owen.context.mobileDeviceMake'),
            Column('mobileDeviceModel', DataType.VARCHAR, length=50, path='owen.context.mobileDeviceModel'),
            Column('notificationEnabledFlag', DataType.BOOLEAN, path='owen.context.notificationEnabledFlag'),
            Column('osFamily', DataType.VARCHAR, length=25, path='owen.context.osFamily'),
            Column('osName', DataType.VARCHAR, length=2048, path='owen.context.osName'),
            Column('osVersion', DataType.VARCHAR, length=2048, path='owen.context.osVersion'),
            Column('pageName', DataType.VARCHAR, length=2048, path='owen.context.pageName'),
            Column('pageType', DataType.VARCHAR, length=100, path='owen.context.pageType'),
            Column('partialSearchTerm', DataType.VARCHAR, length=2048, path='owen.context.partialSearchTerm'),
            Column('personalizationFlag', DataType.BOOLEAN, path='owen.context.personalizationFlag'),
            Column('previousPageName', DataType.VARCHAR, length=2048, path='owen.context.previousPageName'),
            Column('previousViewInstanceUuid', DataType.VARCHAR, length=2048, path='owen.context.previousViewInstanceUuid'),
            Column('promptName', DataType.VARCHAR, length=2048, path='owen.context.promptName'),
            Column('propertyName', DataType.VARCHAR, length=20, path='owen.context.propertyName'),
            Column('referrer', DataType.VARCHAR, length=2048, path='owen.context.referrer'),
            Column('region', DataType.VARCHAR, length=25, path='owen.context.region'),
            Column('screenHeight', DataType.INT, path='owen.context.screenHeight'),
            Column('screenWidth', DataType.INT, path='owen.context.screenWidth'),
            Column('session', DataType.VARCHAR, length=2048, path='owen.context.session'),
            Column('test_testUuid', DataType.VARCHAR, length=26, path='owen.context.test.testUuid'),
            Column('udid', DataType.VARCHAR, length=40, path='owen.context.udid'),
            Column('userAgent', DataType.VARCHAR, length=2048, path='owen.context.userAgent'),
            Column('userQualifier', DataType.VARCHAR, length=26, path='owen.context.userQualifier'),
            Column('userUuid', DataType.VARCHAR, length=2048, path='owen.context.userUuid'),
            Column('vendorObject', DataType.VARCHAR, length=512, path='owen.context.vendor'),
            Column('viewInstanceUuid', DataType.VARCHAR, length=128, path='owen.context.viewInstanceUuid'),
            Column('eventAction', DataType.VARCHAR, length=2048, path='owen.event.eventAction'),
            Column('eventCategory', DataType.VARCHAR, length=25, path='owen.event.eventCategory'),
            Column('eventInstanceUuid', DataType.VARCHAR, length=26, path='owen.event.eventInstanceUuid'),
            Column('eventName', DataType.VARCHAR, length=50, path='owen.event.eventName'),
            Column('eventPlatform', DataType.VARCHAR, length=25, path='owen.event.eventPlatform'),
            Column('eventPlatformVersion', DataType.VARCHAR, length=25, path='owen.event.eventPlatformVersion'),
            Column('eventTarget', DataType.VARCHAR, length=2048, path='owen.event.eventTarget'),
            Column('eventVersion', DataType.VARCHAR, length=25, path='owen.event.eventVersion'),
            Column('eventTimestamp', DataType.DATETIME, date_pattern="yyyy-MM-dd'T'HH:mm:ss'Z'", path='owen.event.eventTimestamp'),
            Column('derivedEventInstanceId', DataType.VARCHAR, length=64, path='metadata.derivedEventInstanceId'),
            Column('owenProcessed', DataType.DATETIME, date_pattern="yyyy-MM-dd'T'HH:mm:ss'Z'", path='metadata.analyticsTopologyFinishTime'),
        ],
    ))))
    print 'created dataset: %s' % dataset.id
