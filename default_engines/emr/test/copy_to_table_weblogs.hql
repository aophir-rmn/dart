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

INSERT INTO TABLE weblogs
PARTITION (year, week, day)
SELECT
ip,
user,
CAST(unix_timestamp(requestDate, "dd/MMM/yyyy:HH:mm:ss Z")*1000 AS TIMESTAMP),
httpMethod,
urlPath,
queryString,
httpVersion,
statusCode,
CAST(bytesSent AS INT),
referrer,
userAgent,
CAST(responseTime AS BIGINT),
hostname,
userFingerprint,
userId,
sessionId,
requestId,
visitorId,
vegSlice,
fruitSlice,
cacheHitMiss,
  year,
  week,
  day
FROM weblogs_stage;
