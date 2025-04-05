from utils.db import get_db

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
    statut ENUM('en_cours', 'en_retard', 'retourne', 'annule') DEFAULT 'en_cours',
    FOREIGN KEY (id_materiel) REFERENCES materiel(id),
    FOREIGN KEY (id_emprunteur) REFERENCES USEUR(ID),
    INDEX idx_materiel (id_materiel),
    INDEX idx_emprunteur (id_emprunteur),
    INDEX idx_statut (statut)
)
"""
get_db(sql_pret)
print("Table pret créée")