CREATE TABLE "reference_values" (
	"ID"	INTEGER,
	"test"	INTEGER NOT NULL,
	"referenceTag"	INTEGER NOT NULL,
	"updated"	DATETIME NOT NULL,
	"duration"	INTEGER NOT NULL,
	"cpu_time"	INTEGER NOT NULL,
	"cpu_usage_avg"	INTEGER NOT NULL,
	"cpu_usage_max"	INTEGER NOT NULL,
	"memory_avg"	INTEGER NOT NULL,
	"memory_max"	INTEGER NOT NULL,
	"io_write"	INTEGER NOT NULL,
	"io_read"	INTEGER NOT NULL,
	"threads_avg"	INTEGER NOT NULL,
	"threads_max"	INTEGER NOT NULL,
	"raw_data"	BLOB NOT NULL,
	CONSTRAINT "UQ_reference" UNIQUE("test","referenceTag"),
	FOREIGN KEY("referenceTag") REFERENCES "referenceTags"("ID"),
	PRIMARY KEY("ID"),
	FOREIGN KEY("test") REFERENCES "tests"("ID")
);
CREATE TABLE "referenceTags" (
	"ID"	INTEGER,
	"tag"	VARCHAR(64) NOT NULL UNIQUE,
	PRIMARY KEY("ID")
);
CREATE TABLE "results" (
	"ID"	INTEGER,
	"test"	INTEGER NOT NULL,
	"job"	INTEGER NOT NULL,
	"result"	INTEGER NOT NULL,
	"start"	DATETIME NOT NULL,
	"duration"	INTEGER NOT NULL,
	"cpu_time"	INTEGER NOT NULL,
	"cpu_usage_avg"	INTEGER NOT NULL,
	"cpu_usage_max"	INTEGER NOT NULL,
	"memory_avg"	INTEGER NOT NULL,
	"memory_max"	INTEGER NOT NULL,
	"io_write"	INTEGER NOT NULL,
	"io_read"	INTEGER NOT NULL,
	"threads_avg"	INTEGER NOT NULL,
	"threads_max"	INTEGER NOT NULL,
	"raw_data"	BLOB NOT NULL,
	"output" BLOB DEFAULT '',
	CONSTRAINT "UQ_test" UNIQUE("test","job"),
	FOREIGN KEY("result") REFERENCES "resultTags"("ID"),
	FOREIGN KEY("job") REFERENCES "jobs"("ID"),
	PRIMARY KEY("ID"),
	FOREIGN KEY("test") REFERENCES "tests"("ID")
);
CREATE TABLE "tests" (
	"ID"	INTEGER,
	"name"	VARCHAR(256) NOT NULL UNIQUE,
	"testset"	VARCHAR(256) NOT NULL,
	"description"	VARCHAR(256) NOT NULL,
	"author"	VARCHAR(256) NOT NULL,
	"frequency"	VARCHAR(256) NOT NULL,
	"graphPath"	VARCHAR(256) NOT NULL,
	"graphXML" BLOB,
	PRIMARY KEY("ID")
);
CREATE TABLE "jobs" (
	"ID"	INTEGER,
	"branch"	VARCHAR(64) NOT NULL,
	"jobnum"	INTEGER NOT NULL,
	"dockerTag"	INTEGER NOT NULL,
	"testScope"	VARCHAR(128) NOT NULL,
	"timestamp_start"	DATETIME NOT NULL,
	"timestamp_end"	DATETIME NOT NULL,
	"result"	INTEGER NOT NULL,
	CONSTRAINT "UQ_job" UNIQUE("branch","jobnum"),
	FOREIGN KEY("result") REFERENCES "resultTags"("ID"),
	FOREIGN KEY("dockerTag") REFERENCES "dockerTags"("ID"),
	PRIMARY KEY("ID")
);
CREATE TABLE "resultTags" (
	"ID"	INTEGER,
	"tag"	VARCHAR(64) NOT NULL UNIQUE,
	"fatal"	BOOLEAN NOT NULL,
	PRIMARY KEY("ID")
);
CREATE TABLE "dockerTags" (
	"ID"	INTEGER,
	"name"	VARCHAR(64) NOT NULL UNIQUE,
	PRIMARY KEY("ID")
);
COMMIT;
