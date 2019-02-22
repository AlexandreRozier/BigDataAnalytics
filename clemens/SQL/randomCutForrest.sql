-- ** Anomaly detection **
-- Compute an anomaly score for each record in the source stream using Random Cut Forest
-- Creates a temporary stream and defines a schema
CREATE OR REPLACE STREAM "TEMP_STREAM" (
--   "APPROXIMATE_ARRIVAL_TIME"     timestamp,
--   "srcaddr"     varchar(16),
--   "dstaddr"   varchar(16),
   "dateminute"   BIGINT,
   "weekdayId"  INT,
   "numberOfRequests"   INT,
   "ANOMALY_SCORE"  DOUBLE,
   "ANOMALY_EXPLANATION"  varchar(512));
   
-- Creates an output stream and defines a schema
CREATE OR REPLACE STREAM "DESTINATION_SQL_STREAM" (
--   "APPROXIMATE_ARRIVAL_TIME"     timestamp,
 --  "srcaddr"     varchar(16),
--   "dstaddr"   varchar(16),
   "dateminute"   BIGINT,
   "weekdayId"  INT,
   "numberOfRequests"        INT,
   "ANOMALY_SCORE"  DOUBLE,
   "ANOMALY_EXPLANATION"  varchar(512));
 
-- Compute an anomaly score for each record in the source stream
-- using Random Cut Forest
-- this is where the anomaly detection happens. See https://docs.aws.amazon.com/kinesisanalytics/latest/sqlref/sqlrf-random-cut-forest-with-explanation.html
CREATE OR REPLACE PUMP "STREAM_PUMP" AS INSERT INTO "TEMP_STREAM"
--  SELECT STREAM "APPROXIMATE_ARRIVAL_TIME", "srcaddr", "dstaddr", "bytes", "ANOMALY_SCORE", "ANOMALY_EXPLANATION"
-- SELECT STREAM "srcaddr", "dstaddr", "bytes", "ANOMALY_SCORE", "ANOMALY_EXPLANATION"
  SELECT STREAM "dateminute", "weekdayId", "numberOfRequests", "ANOMALY_SCORE", "ANOMALY_EXPLANATION" 
  FROM TABLE(RANDOM_CUT_FOREST_WITH_EXPLANATION(
    CURSOR(SELECT STREAM "dateminute", "weekdayId", "numberOfRequests" FROM "SOURCE_SQL_STREAM_001"), 100, 256, 100000, 1, true
  )
);
-- Sort records by descending anomaly score, insert into output stream
CREATE OR REPLACE PUMP "OUTPUT_PUMP" AS INSERT INTO "DESTINATION_SQL_STREAM"
SELECT STREAM * FROM "TEMP_STREAM"
--WHERE ANOMALY_SCORE > 3.0
ORDER BY FLOOR("TEMP_STREAM".ROWTIME TO SECOND), ANOMALY_SCORE DESC;
