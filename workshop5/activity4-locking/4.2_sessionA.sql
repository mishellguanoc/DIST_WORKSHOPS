-- Activity 4.2 — FIX WITH SELECT ... FOR UPDATE — SESSION A  (terminal 1)
-- Copy/paste ONE step at a time, following the global step numbers.

-- [Step 1] A reads AND locks the row (exclusive lock until COMMIT)
START TRANSACTION;
SELECT balance FROM accounts WHERE id=1 FOR UPDATE;

-- (Step 2 happens in Session B: B's SELECT ... FOR UPDATE waits -> take the screenshot)

-- [Step 3] A updates relative to the current value and commits -> releases the lock
UPDATE accounts SET balance = balance + 100 WHERE id=1;
COMMIT;

-- (Step 4 happens in Session B)

-- [Step 5] Final value: 1050
SELECT id, balance FROM accounts WHERE id=1;
