from utils.db import get_db

# Table des localisations
sql_localisation = """
CREATE TABLE IF NOT EXISTS localisation (
    id INT AUTO_INCREMENT PRIMARY KEY,
    batiment VARCHAR(100) NOT NULL,
    etage VARCHAR(50),
    salle VARCHAR(50),
    description TEXT,
    date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_batiment (batiment),
    INDEX idx_etage (etage),
    INDEX idx_salle (salle)
)
"""
get_db(sql_localisation)
print("Table localisation créée")

# Ajout de la colonne id_localisation à la table materiel si elle n'existe pas
columns = get_db("SHOW COLUMNS FROM materiel LIKE 'id_localisation'")
if not columns:
    sql_alter = "ALTER TABLE materiel ADD COLUMN id_localisation INT, ADD FOREIGN KEY (id_localisation) REFERENCES localisation(id)"
    get_db(sql_alter)
    print("Colonne id_localisation ajoutée à la table materiel")