-- Activity 3 — run on mysql-primary
-- Sharding rule (shard key = id): even id -> Shard 1
INSERT INTO users_shard1.users VALUES
  (2, 'Ana Morales',     'ana.morales@example.com',     'Quito'),
  (4, 'Carlos Vega',     'carlos.vega@example.com',     'Guayaquil'),
  (6, 'Lucia Paredes',   'lucia.paredes@example.com',   'Cuenca'),
  (8, 'Diego Andrade',   'diego.andrade@example.com',   'Ibarra');
