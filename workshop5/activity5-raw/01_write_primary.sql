-- Activity 5 / Step 1 — run on mysql-primary (database: lab): write, then read your own write locally
UPDATE accounts SET balance=balance+1 WHERE id=1;
SELECT id, balance, updated_at FROM accounts WHERE id=1;
