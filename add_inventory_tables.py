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

# Ajout d'un index unique sur ID dans la table USEUR si nécessaire
try:
    sql_index = "ALTER TABLE USEUR ADD UNIQUE INDEX idx_user_id (ID)"
    get_db(sql_index)
    print("Index unique ajouté sur la colonne ID de la table USEUR")
except Exception as e:
    if "Duplicate entry" in str(e):
        print("L'index unique existe déjà sur la table USEUR")
    else:
        raise e

# Table des prêts
sql_pret = """
CREATE TABLE IF NOT EXISTS pret (
    id INT AUTO_INCREMENT PRIMARY KEY,
    id_materiel INT NOT NULL,
    id_emprunteur VARCHAR(255) NOT NULL,
    date_emprunt DATETIME DEFAULT CURRENT_TIMESTAMP,
    date_retour_prevue DATE NOT NULL,
    date_retour DATETIME,
    notes TEXT,
    statut ENUM('en_cours', 'en