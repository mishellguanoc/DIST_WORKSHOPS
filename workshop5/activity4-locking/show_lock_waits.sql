-- Optional evidence (terminal 3, run while Session B is waiting):
-- shows which transaction is waiting and which one is blocking it.
SELECT waiting_pid, waiting_query, blocking_pid, blocking_query, wait_age
FROM sys.innodb_lock_waits;
