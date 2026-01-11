-- Initialisation de la base de données GLPI

-- Création de la base de données avec les bonnes propriétés
CREATE DATABASE IF NOT EXISTS glpi_db 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci;

-- Utiliser la base de données
USE glpi_db;

-- Création de la table de configuration initiale
CREATE TABLE IF NOT EXISTS glpi_config (
  id INT PRIMARY KEY,
  version VARCHAR(20),
  install_date DATETIME,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table glpi_users
CREATE TABLE IF NOT EXISTS glpi_users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL UNIQUE,
  realname VARCHAR(255),
  firstname VARCHAR(255),
  password VARCHAR(255),
  email VARCHAR(255),
  phone VARCHAR(20),
  phone2 VARCHAR(20),
  is_active TINYINT(1) DEFAULT 1,
  entities_id INT,
  date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  date_mod TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_entities_id (entities_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table glpi_itilcategories
CREATE TABLE IF NOT EXISTS glpi_itilcategories (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  completename TEXT,
  entities_id INT,
  is_recursive TINYINT(1) DEFAULT 0,
  INDEX idx_entities_id (entities_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table glpi_tickets
CREATE TABLE IF NOT EXISTS glpi_tickets (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  content LONGTEXT,
  status INT DEFAULT 1,
  type TINYINT,
  priority INT,
  urgency INT,
  impact INT,
  itilcategories_id INT,
  entities_id INT,
  users_id_recipient INT,
  date DATETIME DEFAULT CURRENT_TIMESTAMP,
  date_mod DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  solvedate DATETIME,
  closedate DATETIME,
  FOREIGN KEY (itilcategories_id) REFERENCES glpi_itilcategories(id),
  FOREIGN KEY (users_id_recipient) REFERENCES glpi_users(id),
  INDEX idx_entities_id (entities_id),
  INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table glpi_tickets_users
CREATE TABLE IF NOT EXISTS glpi_tickets_users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  tickets_id INT NOT NULL,
  users_id INT NOT NULL,
  type TINYINT,
  use_notification TINYINT(1) DEFAULT 0,
  FOREIGN KEY (tickets_id) REFERENCES glpi_tickets(id) ON DELETE CASCADE,
  FOREIGN KEY (users_id) REFERENCES glpi_users(id) ON DELETE CASCADE,
  UNIQUE KEY unique_ticket_user_type (tickets_id, users_id, type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table glpi_items_tickets
CREATE TABLE IF NOT EXISTS glpi_items_tickets (
  id INT AUTO_INCREMENT PRIMARY KEY,
  tickets_id INT NOT NULL,
  itemtype VARCHAR(100),
  items_id INT,
  FOREIGN KEY (tickets_id) REFERENCES glpi_tickets(id) ON DELETE CASCADE,
  UNIQUE KEY unique_item_ticket (tickets_id, itemtype, items_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table glpi_ticketfollowups
CREATE TABLE IF NOT EXISTS glpi_ticketfollowups (
  id INT AUTO_INCREMENT PRIMARY KEY,
  tickets_id INT NOT NULL,
  users_id INT NOT NULL,
  content LONGTEXT,
  date DATETIME DEFAULT CURRENT_TIMESTAMP,
  is_private TINYINT(1) DEFAULT 0,
  FOREIGN KEY (tickets_id) REFERENCES glpi_tickets(id) ON DELETE CASCADE,
  FOREIGN KEY (users_id) REFERENCES glpi_users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Table glpi_tickettasks
CREATE TABLE IF NOT EXISTS glpi_tickettasks (
  id INT AUTO_INCREMENT PRIMARY KEY,
  tickets_id INT NOT NULL,
  users_id INT NOT NULL,
  content LONGTEXT,
  state INT,
  date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
  date DATETIME,
  date_end DATETIME,
  FOREIGN KEY (tickets_id) REFERENCES glpi_tickets(id) ON DELETE CASCADE,
  FOREIGN KEY (users_id) REFERENCES glpi_users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insertion de la version initiale
INSERT IGNORE INTO glpi_config (id, version) VALUES (1, '10.0.0');

-- Définition des droits pour l'utilisateur GLPI
GRANT ALL PRIVILEGES ON glpi_db.* TO 'glpi_user'@'%';
FLUSH PRIVILEGES;
