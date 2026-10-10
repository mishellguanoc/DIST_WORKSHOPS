-- Activity 5 / Step 3 — run on mysql-primary: every committed transaction so far, including Step 1's write.
-- This GTID set is the "token" that identifies the state the client has written.
SELECT @@GLOBAL.gtid_executed\G
