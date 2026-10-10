-- Activity 4.1 — LOST UPDATE — SESSION A  (terminal 1)
-- Copy/paste ONE step at a time, following the global step numbers (A and B alternate).
-- Do not pipe this file: the point is to interleave the two sessions by hand.

-- [Step 1] A reads 1000
SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED;
START TRANSACTION;
SELECT balance FROM accounts WHERE id=1;

-- (Step 2 happens in Session B: B also reads 1000)

-- [Step 3] A writes its application-computed value 1000 + 100 (literal, naive read-modify-write)
UPDATE accounts SET balance=1100 WHERE id=1;

-- (Step 4 happens in Session B: B's UPDATE blocks on A's row lock)

-- [Step 5] A commits -> B's blocked UPDATE continues immediately
COMMIT;

-- (Step 6 happens in Session B: B commits)

-- [Step 7] Check the final value (expected 1050, observed 950 -> A's +100 was lost)
SELECT id, balance FROM accounts WHERE id=1;
