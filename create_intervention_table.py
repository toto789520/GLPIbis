from utils.db import get_db

# Table des interventions
sql_intervention = """
CREATE TABLE IF NOT EXISTS intervention (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_materiel INT NOT NULL,
    id_technicien VARCHAR(255) NOT NULL,
    type_intervention ENUM('maintenance', 'reparation', 'mise_a_jour', 'autre') NOT NULL,
    description TEXT NOT NULL,
    date_intervention DATETIME DEFAULT CURRENT_TIMESTAMP,
    date_fin DATETIME,
    statut ENUM('en_cours', 'termine') DEFAULT 'en_cours',
    FOREIGN KEY (id_materiel) REFERENCES materiel(id),
    FOREIGN KEY (id_technicien) REFERENCES USEUR(ID),
    INDEX idx_materiel (id_materiel),
    INDEX idx_technicien (id_technicien),
    INDEX idx_type (type_intervention),
    INDEX idx_statut (statut)
)
"""
get_db(sql_intervention)
print("Table intervention créée")

# Table pour les sous-tickets
get_db("""
CREATE TABLE IF NOT EXISTS sous_tickets (
    id VARCHAR(36) PRIMARY KEY,
    parent_ticket_id VARCHAR(36) NOT NULL,
    titre VARCHAR(255) NOT NULL,
    description TEXT,
    statut ENUM('nouveau', 'en_cours', 'en_attente', 'resolu', 'ferme') DEFAULT 'nouveau',
    priorite INT DEFAULT 5,
    assigne_a VARCHAR(255),
    date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
    date_modification DATETIME ON UPDATE CURRENT_TIMESTAMP,
    date_resolution DATETIME,
    createur_id VARCHAR(255) NOT NULL,
    FOREIGN KEY (parent_ticket_id) REFERENCES tiqué(ID_tiqué),
    FOREIGN KEY (assigne_a) REFERENCES USEUR(ID),
    FOREIGN KEY (createur_id) REFERENCES USEUR(ID)
)
""")

# Table pour les dépendances entre sous-tickets
get_db("""
CREATE TABLE IF NOT EXISTS sous_tickets_dependances (
    sous_ticket_id VARCHAR(36),
    depend_de_id VARCHAR(36),
    PRIMARY KEY (sous_ticket_id, depend_de_id),
    FOREIGN KEY (sous_ticket_id) REFERENCES sous_tickets(id),
    FOREIGN KEY (depend_de_id) REFERENCES sous_tickets(id)
)
""")

# Table pour les commentaires sur les sous-tickets
get_db("""
CREATE TABLE IF NOT EXISTS sous_tickets_commentaires (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sous_ticket_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    commentaire TEXT NOT NULL,
    date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sous_ticket_id) REFERENCES sous_tickets(id),
    FOREIGN KEY (user_id) REFERENCES USEUR(ID)
)
""")

# Table pour l'historique des modifications des sous-tickets
get_db("""
CREATE TABLE IF NOT EXISTS sous_tickets_historique (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sous_ticket_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    type_modification ENUM('creation', 'statut', 'priorite', 'assignation', 'autre') NOT NULL,
    ancienne_valeur TEXT,
    nouvelle_valeur TEXT,
    date_modification DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sous_ticket_id) REFERENCES sous_tickets(id),
    FOREIGN KEY (user_id) REFERENCES USEUR(ID)
)
""")

# Ajout d'une colonne pour compter les sous-tickets dans la table tiqué si elle n'existe pas
columns = get_db("SHOW COLUMNS FROM tiqué LIKE 'nombre_sous_tickets'")
if not columns:
    get_db("ALTER TABLE tiqué ADD COLUMN nombre_sous_tickets INT DEFAULT 0")
    print("Colonne nombre_sous_tickets ajoutée à la table tiqué")

print("Tables pour les sous-tickets créées avec succès")