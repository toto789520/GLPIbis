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