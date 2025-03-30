from utils.db import get_db

# Vérifier si la colonne existe déjà
columns = get_db("SHOW COLUMNS FROM USEUR LIKE 'role'")
if not columns:
    print("Ajout de la colonne 'role' à la table USEUR...")
    get_db("ALTER TABLE USEUR ADD COLUMN role VARCHAR(20) DEFAULT 'user'")
    print("Colonne 'role' ajoutée avec succès")
else:
    print("La colonne 'role' existe déjà dans la table USEUR")

# Définir un utilisateur comme admin pour tests
admin_user_id = get_db("SELECT ID FROM USEUR LIMIT 1")[0][0]
get_db("UPDATE USEUR SET role = 'admin' WHERE ID = %s", (admin_user_id,))
print(f"Utilisateur {admin_user_id} défini comme administrateur")

# Vérification finale
user_info = get_db("SELECT ID, name, role FROM USEUR WHERE ID = %s", (admin_user_id,))
if user_info:
    user = user_info[0]
    print(f"User ID: {user[0]}")
    print(f"Name: {user[1]}")
    print(f"Role: {user[2]}")

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