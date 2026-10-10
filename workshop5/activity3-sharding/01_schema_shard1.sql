-- Activity 3 / Horizontal sharding — run on mysql-primary (Shard 1)
-- Same schema on every shard: horizontal fragments split ROWS, not columns.
CREATE DATABASE IF NOT EXISTS users_shard1;
CREATE TABLE IF NOT EXISTS users_shard1.users
(id INT PRIMARY KEY, name VARCHAR(50), email VARCHAR(80), city VARCHAR(50));
