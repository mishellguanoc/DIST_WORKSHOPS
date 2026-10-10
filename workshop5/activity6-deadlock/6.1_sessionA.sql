-- Activity 6.1 — DEADLOCK — SESSION A  (terminal 1)
-- Copy/paste ONE step at a time, following the global step numbers (A and B alternate).

-- [Step 1] A locks row 1
START TRANSACTION;
UPDATE accounts SET balance=balance+10 WHERE id=1;

-- (Step 2 happens in Session B: B locks row 2)

-- [Step 3] A asks for row 2, held by B -> A WAITS (normal blocking, not yet a deadlock)
UPDATE accounts SET balance=balance-10 WHERE id=2;

-- (Step 4 happens in Session B: B asks for row 1, held by A -> cycle A->B->A -> deadlock.
--  InnoDB detects it at once, rolls back one transaction (the victim, usually B) with ERROR 1213,
--  and A's waiting UPDATE above then completes.)

-- [Step 5] Survivor commits (if A was the victim instead, run ROLLBACK here)
COMMIT;
SELECT id, balance FROM accounts;
