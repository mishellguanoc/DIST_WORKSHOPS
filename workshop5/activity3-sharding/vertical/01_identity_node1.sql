-- Activity 3 Challenge / Vertical sharding — run on mysql-primary (Node 1)
-- Vertical fragments split COLUMNS. Node 1 keeps the identity fragment: who the user is.
-- Every fragment repeats the primary key (id) so the full row can be rebuilt with a join (lossless).
CREATE DATABASE IF NOT EXISTS users_identity;
CREATE TABLE IF NOT EXISTS users_identity.identity
(id INT PRIMARY KEY, name VARCHAR(50) NOT NULL);

INSERT INTO users_identity.identity VALUES
  (1,'Mateo Salazar'), (2,'Ana Morales'), (3,'Valeria Ortiz'), (4,'Carlos Vega'),
  (5,'Sofia Herrera'), (6,'Lucia Paredes'), (7,'Andres Cevallos'), (8,'Diego Andrade');
