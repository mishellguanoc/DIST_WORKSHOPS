-- Activity 6.2 — PREVENTION WITH CONSISTENT LOCK ORDER — SESSION A  (terminal 1)
-- Run 00_reset.sql first. Copy/paste ONE step at a time.

-- [Step 1] A locks BOTH rows up front, always in the same order (ORDER BY id): row 1, then row 2
START TRANSACTION;
SELECT * FROM accounts WHERE id IN (1,2) ORDER BY id FOR UPDATE;

-- (Step 2 happens in Session B: B requests the same rows in the same order -> it just WAITS)

-- [Step 3] A performs its updates and commits -> releases both locks
UPDATE accounts SET balance=balance+10 WHERE id=1;
UPDATE accounts SET balance=balance-10 WHERE id=2;
COMMIT;

-- (Step 4 happens in Session B)

-- [Step 5] Final state: id 1 = 1020, id 2 = 980, and no ERROR 1213 anywhere
SELECT id, balance FROM accounts;
