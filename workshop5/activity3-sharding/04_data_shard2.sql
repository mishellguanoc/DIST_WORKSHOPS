-- Activity 3 — run on mysql-shard2
-- Sharding rule (shard key = id): odd id -> Shard 2
INSERT INTO users_shard2.users VALUES
  (1, 'Mateo Salazar',   'mateo.salazar@example.com',   'Quito'),
  (3, 'Valeria Ortiz',   'valeria.ortiz@example.com',   'Loja'),
  (5, 'Sofia Herrera',   'sofia.herrera@example.com',   'Ambato'),
  (7, 'Andres Cevallos', 'andres.cevallos@example.com', 'Urcuqui');
