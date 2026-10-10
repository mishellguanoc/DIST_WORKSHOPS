-- Activity 6.2 — PREVENTION WITH CONSISTENT LOCK ORDER — SESSION B  (terminal 2)
-- Copy/paste ONE step at a time.

-- (Step 1 happens in Session A: A holds rows 1 and 2)

-- [Step 2] Same rows, same order -> B BLOCKS on row 1 while holding nothing, so no cycle can form.
--          Screenshot the waiting cursor, then go to Session A for Step 3 within 50 s.
START TRANSACTION;
SELECT * FROM accounts WHERE id IN (1,2) ORDER BY id FOR UPDATE;
-- ...returns as soon as A commits, showing A's committed values (1010 / 990)

-- [Step 4] B performs its updates and commits
UPDATE accounts SET balance=balance-10 WHERE id=2;
UPDATE accounts SET balance=balance+10 WHERE id=1;
COMMIT;
SELECT id, balance FROM accounts;
