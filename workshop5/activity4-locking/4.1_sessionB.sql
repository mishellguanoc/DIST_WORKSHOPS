-- Activity 4.1 — LOST UPDATE — SESSION B  (terminal 2)
-- Copy/paste ONE step at a time, following the global step numbers (A and B alternate).

-- (Step 1 happens in Session A: A reads 1000)

-- [Step 2] B reads 1000 too (A has not committed anything yet)
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
START TRANSACTION;
SELECT balance FROM accounts WHERE id=1;

-- (Step 3 happens in Session A: A writes 1100, still uncommitted)

-- [Step 4] B writes its application-computed value 1000 - 50.
--          This BLOCKS: A holds the row's exclusive lock. Go to Session A for Step 5
--          within 50 s (innodb_lock_wait_timeout), or B gets ERROR 1205.
UPDATE accounts SET balance=950 WHERE id=1;

-- (Step 5 happens in Session A: A commits -> this UPDATE finishes and overwrites 1100 with 950)

-- [Step 6] B commits
COMMIT;
SELECT id, balance FROM accounts WHERE id=1;
