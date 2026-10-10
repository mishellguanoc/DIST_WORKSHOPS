-- Activity 5 / Step 4 — run INTERACTIVELY on mysql-replica:
--   docker exec -it mysql-replica mysql -uroot -proot
-- Replace the placeholder with the GTID set copied from Step 3.
-- Returns 0 once the replica has applied that whole set, 1 if 5 seconds pass first (timeout).
SELECT WAIT_FOR_EXECUTED_GTID_SET('<PASTE_GTID_SET_HERE>', 5);
USE lab;
SELECT id, balance, updated_at FROM accounts WHERE id=1;
