SET hive.error.on.empty.partition = true;
SET hive.exec.dynamic.partition = true;
SET hive.exec.dynamic.partition.mode = nonstrict;
SET hive.exec.max.created.files = 20000;
SET hive.exec.max.dynamic.partitions.pernode = 3000;
SET hive.exec.max.dynamic.partitions = 30000;
SET hive.hadoop.supports.splittable.combineinputformat = true;
SET hive.merge.mapfiles = true;
SET hive.merge.mapredfiles = true;
SET hive.merge.size.per.task = 256000000;
SET hive.merge.smallfiles.avgsize = 64000000;
SET hive.optimize.s3.query = true;
SET hive.optimize.sort.dynamic.partition = false;
SET mapred.child.java.opts = -Xmx1g;
SET mapred.child.ulimit = 2000000;
SET mapred.job.shuffle.input.buffer.percent = 0.2;
SET mapred.max.split.size = 1000000000;
SET mapred.min.split.size = 64000000;
SET mapreduce.map.java.opts = -Xmx1024m -XX:-UseGCOverheadLimit -Xss128m;
SET mapreduce.map.memory.mb = 1600;
SET parquet.block.size = 65217728;

SET hive.exec.compress.output=true;
SET mapred.output.compression.type=BLOCK;
SET mapred.output.compression.codec=org.apache.hadoop.io.compress.GzipCodec;

INSERT INTO TABLE owen_eu
PARTITION (year, week, day)
SELECT
get_json_object(json, '$.metadata.host'),
get_json_object(json, '$.owen.context.pageName'),
get_json_object(json, '$.owen.context.viewInstanceUuid'),
get_json_object(json, '$.owen.context.previousPageName'),
get_json_object(json, '$.owen.context.previousViewInstanceUuid'),
get_json_object(json, '$.owen.context.session'),
get_json_object(json, '$.owen.context.pageType'),
get_json_object(json, '$.owen.context.propertyName'),
get_json_object(json, '$.owen.context.environment'),
CAST(get_json_object(json, '$.owen.context.appForegroundFlag') AS BOOLEAN),
CAST(get_json_object(json, '$.owen.context.bluetoothEnabledFlag') AS BOOLEAN),
CAST(get_json_object(json, '$.owen.context.favoriteFlag') AS BOOLEAN),
CAST(get_json_object(json, '$.owen.context.locationEnabledFlag') AS BOOLEAN),
CAST(get_json_object(json, '$.owen.context.loggedInFlag') AS BOOLEAN),
CAST(get_json_object(json, '$.owen.context.notificationEnabledFlag') AS BOOLEAN),
CAST(get_json_object(json, '$.owen.context.personalizationFlag') AS BOOLEAN),
get_json_object(json, '$.owen.context.advertiserUuid'),
get_json_object(json, '$.owen.context.udid'),
get_json_object(json, '$.owen.context.userQualifier'),
get_json_object(json, '$.owen.context.custom.legacy.userId'),
get_json_object(json, '$.owen.context.userUuid'),
get_json_object(json, '$.owen.context.macAddress'),
get_json_object(json, '$.owen.context.ipAddress'),
get_json_object(json, '$.owen.context.osVersion'),
get_json_object(json, '$.owen.context.osFamily'),
get_json_object(json, '$.owen.context.osName'),
get_json_object(json, '$.owen.context.browserFamily'),
get_json_object(json, '$.owen.context.deviceCategory'),
get_json_object(json, '$.owen.context.mobileDeviceMake'),
get_json_object(json, '$.owen.context.mobileDeviceModel'),
get_json_object(json, '$.owen.context.connectionType'),
get_json_object(json, '$.owen.context.userAgent'),
get_json_object(json, '$.owen.context.custom.legacy.geofenceId'),
CAST(unix_timestamp(get_json_object(json, '$.owen.event.eventTimestamp'), "yyyy-MM-dd'T'HH:mm:ssZ")*1000 AS TIMESTAMP),
get_json_object(json, '$.owen.event.eventInstanceUuid'),
get_json_object(json, '$.owen.event.eventPlatformVersion'),
get_json_object(json, '$.owen.event.eventVersion'),
get_json_object(json, '$.owen.event.eventCategory'),
get_json_object(json, '$.owen.event.eventName'),
get_json_object(json, '$.owen.event.eventAction'),
get_json_object(json, '$.owen.event.eventPlatform'),
CAST(CAST(get_json_object(json, '$.some.fake.path.testUnixTimestampSecondsPattern') AS BIGINT)*1000 AS TIMESTAMP),
CAST(CAST(get_json_object(json, '$.some.fake.path.testUnixTimestampMillisPattern') AS BIGINT) AS TIMESTAMP),
  year,
  week,
  day
FROM owen_eu_stage;
