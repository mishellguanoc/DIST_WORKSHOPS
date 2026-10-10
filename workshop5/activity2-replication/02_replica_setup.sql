-- Activity 2 / Step 2 — run on mysql-replica
-- SOURCE_HOST uses the Docker service name: containers resolve each other by name on the compose network.
-- SOURCE_AUTO_POSITION=1: GTID-based positioning, the replica asks for every GTID it has not executed yet
--   (no binlog file name / offset needed).
-- GET_SOURCE_PUBLIC_KEY=1: lets the 'repl' user authenticate with caching_sha2_password over a non-TLS link.
STOP REPLICA;
CHANGE REPLICATION SOURCE TO
  SOURCE_HOST='mysql-primary',
  SOURCE_USER='repl',
  SOURCE_PASSWORD='repl',
  SOURCE_AUTO_POSITION=1,
  GET_SOURCE_PUBLIC_KEY=1;
START REPLICA;
