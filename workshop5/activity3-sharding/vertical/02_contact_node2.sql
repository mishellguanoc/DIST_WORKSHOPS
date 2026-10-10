-- Activity 3 Challenge / Vertical sharding — run on mysql-shard2 (Node 2)
-- Node 2 keeps the contact/profile fragment: how to reach the user and where they live.
CREATE DATABASE IF NOT EXISTS users_contact;
CREATE TABLE IF NOT EXISTS users_contact.contact
(id INT PRIMARY KEY, email VARCHAR(80), city VARCHAR(50));

INSERT INTO users_contact.contact VALUES
  (1,'mateo.salazar@example.com','Quito'),     (2,'ana.morales@example.com','Quito'),
  (3,'valeria.ortiz@example.com','Loja'),      (4,'carlos.vega@example.com','Guayaquil'),
  (5,'sofia.herrera@example.com','Ambato'),    (6,'lucia.paredes@example.com','Cuenca'),
  (7,'andres.cevallos@example.com','Urcuqui'), (8,'diego.andrade@example.com','Ibarra');
