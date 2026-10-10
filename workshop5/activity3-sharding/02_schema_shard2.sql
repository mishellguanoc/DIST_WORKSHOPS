-- Activity 3 / Horizontal sharding — run on mysql-shard2 (Shard 2)
CREATE DATABASE IF NOT EXISTS users_shard2;
CREATE TABLE IF NOT EXISTS users_shard2.users
(id INT PRIMARY KEY, name VARCHAR(50), email VARCHAR(80), city VARCHAR(50));
