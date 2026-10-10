-- Activity 4.2 — FIX WITH SELECT ... FOR UPDATE — SESSION B  (terminal 2)
-- Copy/paste ONE step at a time, following the global step numbers.

-- (Step 1 happens in Session A: A locks row 1)

-- [Step 2] B asks for the same lock -> it WAITS (cursor hangs, no result).
--          Screenshot now. Then go to Session A for Step 3 within 50 s.
START TRANSACTION;
SELECT balance FROM accounts WHERE id=1 FOR UPDATE;
-- ...when A commits, this returns 1100 (the current, committed value, not the stale 1000)

-- [Step 4] B updates on top of A's result and commits
UPDATE accounts SET balance = balance - 50 WHERE id=1;
COMMIT;
SELECT id, balance FROM accounts WHERE id=1;
