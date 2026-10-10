-- Activity 5 / Step 2 — run on mysql-replica (database: lab) IMMEDIATELY after Step 1.
-- Replication is asynchronous: this may still show the old balance (stale read) or already the new one.
SELECT id, balance, updated_at FROM accounts WHERE id=1;
