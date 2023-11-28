DROP TABLE IF EXISTS results;
DROP TABLE IF EXISTS reference_values;
DROP TABLE IF EXISTS jobs;
DROP TABLE IF EXISTS tests;
DROP TABLE IF EXISTS dockerTags;
DROP TABLE IF EXISTS resultTags;
DROP TABLE IF EXISTS referenceTags;

CREATE TABLE resultTags (
  ID INTEGER AUTO_INCREMENT,
  tag  VARCHAR(64) NOT NULL UNIQUE,
  fatal  BOOLEAN NOT NULL,
  PRIMARY KEY(ID)
);

CREATE TABLE dockerTags (
  ID  INTEGER AUTO_INCREMENT,
  name  VARCHAR(64) NOT NULL UNIQUE,
  PRIMARY KEY(ID)
);

CREATE TABLE referenceTags (
  ID  INTEGER AUTO_INCREMENT,
  tag  VARCHAR(64) NOT NULL UNIQUE,
  PRIMARY KEY(ID)
);

CREATE TABLE tests (
  ID  INTEGER AUTO_INCREMENT,
  name  VARCHAR(256) NOT NULL UNIQUE,
  testset  VARCHAR(256) NOT NULL,
  description  VARCHAR(256) NOT NULL,
  author  VARCHAR(256) NOT NULL,
  frequency  VARCHAR(256) NOT NULL,
  graphPath  VARCHAR(256) NOT NULL,
  graphXML MEDIUMBLOB,
  PRIMARY KEY(ID)
);

CREATE TABLE test_graph (
  `ID` int NOT NULL AUTO_INCREMENT,
  `test` int NOT NULL,
  `graph` text NOT NULL,
  PRIMARY KEY (`ID`),
  KEY `fk_test_idx` (`test`),
  CONSTRAINT `fk_test` FOREIGN KEY (`test`) REFERENCES `tests` (`ID`)
);

CREATE TABLE jobs (
  ID  INTEGER AUTO_INCREMENT,
  branch  VARCHAR(64) NOT NULL,
  jobnum  INTEGER NOT NULL,
  dockerTag  INTEGER NOT NULL,
  testScope  VARCHAR(128) NOT NULL,
  timestamp_start  DATETIME NOT NULL,
  timestamp_end  DATETIME NOT NULL,
  result  INTEGER NOT NULL,
  CONSTRAINT UQ_job UNIQUE(branch,jobnum),
  FOREIGN KEY(result) REFERENCES resultTags(ID) ON DELETE CASCADE,
  FOREIGN KEY(dockerTag) REFERENCES dockerTags(ID),
  PRIMARY KEY(ID)
);

CREATE TABLE reference_values (
  ID  INTEGER AUTO_INCREMENT,
  test  INTEGER NOT NULL,
  referenceTag  INTEGER DEFAULT 1,
  updated  DATETIME NOT NULL,
  duration  INTEGER NOT NULL,
  cpu_time  INTEGER NOT NULL,
  cpu_usage_avg  INTEGER NOT NULL,
  cpu_usage_max  INTEGER NOT NULL,
  memory_avg  INTEGER NOT NULL,
  memory_max  INTEGER NOT NULL,
  io_write  INTEGER NOT NULL,
  io_read  INTEGER NOT NULL,
  threads_avg  INTEGER NOT NULL,
  threads_max  INTEGER NOT NULL,
  raw_data  MEDIUMBLOB NOT NULL,
  CONSTRAINT UQ_reference UNIQUE(test,referenceTag),
  FOREIGN KEY(referenceTag) REFERENCES referenceTags(ID),
  PRIMARY KEY(ID),
  FOREIGN KEY(test) REFERENCES tests(ID)
);

CREATE TABLE results (
  ID  INTEGER AUTO_INCREMENT,
  test  INTEGER NOT NULL,
  job  INTEGER NOT NULL,
  result  INTEGER NOT NULL,
  start  DATETIME NOT NULL,
  duration  INTEGER NOT NULL,
  cpu_time  INTEGER NOT NULL,
  cpu_usage_avg  INTEGER NOT NULL,
  cpu_usage_max  INTEGER NOT NULL,
  memory_avg  INTEGER NOT NULL,
  memory_max  INTEGER NOT NULL,
  io_write  INTEGER NOT NULL,
  io_read  INTEGER NOT NULL,
  threads_avg  INTEGER NOT NULL,
  threads_max  INTEGER NOT NULL,
  raw_data  MEDIUMBLOB NOT NULL,
  output     MEDIUMBLOB,
  CONSTRAINT UQ_test UNIQUE(test,job),
  FOREIGN KEY(result) REFERENCES resultTags(ID),
  FOREIGN KEY(job) REFERENCES jobs(ID),
  PRIMARY KEY(ID),
  FOREIGN KEY(test) REFERENCES tests(ID)
);

-- Cleanup needed on DB restore
-- DELETE results FROM results INNER JOIN jobs ON results.job = jobs.ID WHERE jobs.branch NOT IN ('8.0.0.', '9.0.0', '8.0.0-reference');
-- DELETE FROM jobs WHERE jobs.branch NOT IN ('8.0.0.', '9.0.0', '8.0.0-reference');