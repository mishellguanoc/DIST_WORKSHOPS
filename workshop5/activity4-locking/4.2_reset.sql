-- Activity 4.2 — reset before the locking fix (run on mysql-primary, database: lab)
UPDATE accounts SET balance=1000 WHERE id=1;
