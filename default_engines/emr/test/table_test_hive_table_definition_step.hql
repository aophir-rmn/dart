
CREATE TABLE IF NOT EXISTS test_hive_table_definition_step (
ip STRING,
  user STRING,
  requestDate TIMESTAMP,
  httpMethod STRING,
  urlPath STRING,
  queryString STRING,
  httpVersion STRING,
  statusCode STRING,
  bytesSent INT,
  referrer STRING,
  userAgent STRING,
  responseTime INT,
  hostname STRING,
  userFingerprint STRING,
  userId STRING,
  sessionId STRING,
  requestId STRING,
  visitorId STRING,
  vegSlice STRING,
  fruitSlice STRING,
  cacheHitMiss STRING
)
PARTITIONED BY (year STRING, week STRING)
ROW FORMAT SERDE 'org.apache.hadoop.hive.contrib.serde2.RegexSerDe'
WITH SERDEPROPERTIES ("input.regex" = "(?<ip>^(?:(?:unknown(?:,\\s)?|(?:\\d+\\.\\d+\\.\\d+\\.\\d+(?:,\\s)?))+)|\\S*)\\s+\\S+\\s+(?<userIdentifier>(?:[^\\[]+|\\$\\S+\\['\\S+'\\]|\\[username\\]))\\s*\\s+\\[(?<requestDate>[^\\]]+)\\]\\s+\"(?<httpMethod>(?:GET|HEAD|POST|PUT|DELETE|TRACE))\\s(?<urlPath>(?:[^ ?]+))(?:\\?(?<queryString>(?:[^ ]+)))?\\sHTTP/(?<httpVersion>(?:[\\d\\.]+))\"\\s+(?<statusCode>[0-9]+)\\s+(?<bytesSent>\\S+)\\s+\"(?<referrer>(?:[^\"\\\\]*(?:\\\\.[^\"\\\\]*)*))\"\\s+\"(?<userAgent>(?:[^\"\\\\]*(?:\\\\.[^\"\\\\]*)*))\"\\s+(?<responseTime>[-0-9]*)\\s+\"(?<hostName>(?:[^\"\\\\]*(?:\\\\.[^\"\\\\]*)*))\"\\s+\"(?<userFingerprint>(?:[^\"\\\\]*(?:\\\\.[^\"\\\\]*)*))\"\\s+\"(?<userId>(?:[^\"\\\\]*(?:\\\\.[^\"\\\\]*)*))\"\\s+\"(?<sessionId>(?:[^\"\\\\]*(?:\\\\.[^\"\\\\]*)*))\"\\s+\"(?<requestId>(?:[^\"\\\\]*(?:\\\\.[^\"\\\\]*)*))\"\\s+\"(?<visitorId>(?:[^\"\\\\]*(?:\\\\.[^\"\\\\]*)*))\"\\s+\"(?<vegSlice>(?:[^\"\\\\]*(?:\\\\.[^\"\\\\]*)*))\"\\s+\"(?<fruitSlice>(?:[^\"\\\\]*(?:\\\\.[^\"\\\\]*)*))\"\\s+\"(?<cacheHitMiss>(?:[^\"\\\\]*(?:\\\\.[^\"\\\\]*)*))\"\\s*\\Z", "output.format.string" = "%1$s %2$s %3$s %4$s %5$s %6$s %7$s %8$s %9$s %10$s %11$s %12$s %13$s %14$s %15$s %16$s %17$s %18$s %19$s %20$s %21s")
TBLPROPERTIES ('skip.header.line.count'='0');
