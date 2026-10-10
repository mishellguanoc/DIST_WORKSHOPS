-- Activity 6 — reset both balances (run on mysql-primary, database: lab) before 6.1 and before 6.2
UPDATE accounts SET balance=1000 WHERE id IN (1,2);
SELECT id, owner, balance FROM accounts;
