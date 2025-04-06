from utils.db import get_db

# Ajout des nouvelles colonnes pour améliorer les profils utilisateurs
columns_to_add = [
    ("role", "VARCHAR(20) DEFAULT 'user'"),
    ("statut", "ENUM('actif', 'inactif') DEFAULT 'actif'"),
    ("derniere_connexion", "DATETIME"),
    ("service", "VARCHAR(100)"),
    ("type_utilisateur", "ENUM('eleve', 'enseignant', 'personnel', 'admin') DEFAULT 'eleve'")
]

for col_name, col_def in columns_to_add:
    columns = get_db(f"SHOW COLUMNS FROM USEUR LIKE '{col_name}'")
    if not columns:
        print(f"Ajout de la colonne '{col_name}' à la table USEUR...")
        get_db(f"ALTER TABLE USEUR ADD COLUMN {col_name} {col_def}")
        print(f"Colonne '{col_name}' ajoutée avec succès")
    else:
        print(f"La colonne '{col_name}' existe déjà dans la table USEUR")

# Définir un utilisateur comme admin pour tests
admin_user_info = get_db("SELECT ID FROM USEUR LIMIT 1")
if admin_user_info:
    admin_user_id = admin_user_info[0][0]
    get_db("UPDATE USEUR SET role = 'admin' WHERE ID = %s", (admin_user_id,))
    print(f"Utilisateur {admin_user_id} défini comme administrateur")

    # Vérification finale
    user_info = get_db("SELECT ID, name, role FROM USEUR WHERE ID = %s", (admin_user_id,))
    if user_info:
        user = user_info[0]
        print(f"User ID: {user[0]}")
        print(f"Name: {user[1]}")
        print(f"Role: {user[2]}")
else:
    print("Aucun utilisateur trouvé dans la table USEUR.")

# Création des tables nécessaires
print("\nCréation des tables supplémentaires...")

# Création de la table activity_logs si elle n'existe pas
get_db("""
    CREATE TABLE IF NOT EXISTS activity_logs (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id VARCHAR(255) NOT NULL,
        action_type VARCHAR(50) NOT NULL,
        module VARCHAR(50) NOT NULL,
        description TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_user_id (user_id),
        INDEX idx_timestamp (timestamp)
    )
""")
print("Table activity_logs vérifiée")

# Création de la table pour les permissions
get_db("""
    CREATE TABLE IF NOT EXISTS user_permissions (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id VARCHAR(255) NOT NULL,
        permissions TEXT NOT NULL,
        UNIQUE KEY unique_user (user_id)
    )
""")
print("Table user_permissions vérifiée")

# Création de la table de groupes
get_db("""
    CREATE TABLE IF NOT EXISTS groupes (
        id INT AUTO_INCREMENT PRIMARY KEY,
        nom VARCHAR(100) NOT NULL,
        description TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
""")
print("Table groupes vérifiée")

# Table d'association utilisateurs-groupes
get_db("""
    CREATE TABLE IF NOT EXISTS user_groups (
        user_id VARCHAR(255) NOT NULL,
        group_id INT NOT NULL,
        PRIMARY KEY (user_id, group_id),
        FOREIGN KEY (user_id) REFERENCES USEUR(ID),
        FOREIGN KEY (group_id) REFERENCES groupes(id),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
""")
print("Table user_groups vérifiée")

print("\nStructure de la base de données mise à jour avec succès")