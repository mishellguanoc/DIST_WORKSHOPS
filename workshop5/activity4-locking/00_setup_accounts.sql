-- Activity 4 — run on mysql-primary (database: lab). Creates the accounts used in Activities 4, 5 and 6.
DROP TABLE IF EXISTS accounts;
CREATE TABLE accounts (
  id INT PRIMARY KEY, owner VARCHAR(50), balance INT NOT NULL,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;
INSERT INTO accounts VALUES (1,'Alice',1000,NOW()),(2,'Bob',1000,NOW());
