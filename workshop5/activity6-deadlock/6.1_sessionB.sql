-- Activity 6.1 — DEADLOCK — SESSION B  (terminal 2)
-- Copy/paste ONE step at a time, following the global step numbers (A and B alternate).

-- (Step 1 happens in Session A: A locks row 1)

-- [Step 2] B locks row 2
START TRANSACTION;
UPDATE accounts SET balance=balance-10 WHERE id=2;

-- (Step 3 happens in Session A: A waits for row 2)

-- [Step 4] B asks for row 1, held by A -> circular wait -> expected:
--   ERROR 1213 (40001): Deadlock found when trying to get lock; try restarting transaction
UPDATE accounts SET balance=balance+10 WHERE id=1;

-- [Step 5] The victim's whole transaction was already rolled back by InnoDB; ROLLBACK just closes it.
ROLLBACK;
