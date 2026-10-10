-- Activity 2 / Step 3 — run on mysql-primary (database: lab)
-- Written only on the primary; it must appear on the replica through replication.
CREATE TABLE IF NOT EXISTS replication_test (id INT PRIMARY KEY, note VARCHAR(80));
INSERT INTO replication_test VALUES (1,'created on primary');
