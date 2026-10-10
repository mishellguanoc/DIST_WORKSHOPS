-- Activity 2 / Step 1 — run on mysql-primary
-- Dedicated account the replica uses to connect to the primary and stream the binary log.
-- REPLICATION SLAVE is the only privilege it needs (least privilege).
CREATE USER IF NOT EXISTS 'repl'@'%' IDENTIFIED BY 'repl';
GRANT REPLICATION SLAVE ON *.* TO 'repl'@'%';
FLUSH PRIVILEGES;
