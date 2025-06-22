"""
Script de création et mise à jour de la structure des tickets
"""
import os
import sys
import json

# Ajouter le répertoire parent au path pour permettre les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.db_manager import DBManager, get_db, init_db_manager

def load_config():
    """Charge la configuration depuis le fichier conf.conf"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'conf.conf')
    try:
        with open(config_path) as f:
            return json.load(f)
    except:
        return {"db_type": "sqlite"}

def create_tickets_table():
    """Crée ou met à jour la table des tickets avec la nouvelle structure"""
    # Initialisation du gestionnaire de BDD
    config = load_config()
    db_type = config.get('db_type', 'sqlite')
    mysql_params = config.get('mysql', {}) if db_type == 'mysql' else None
    
    global db_manager
    db_manager = init_db_manager(db_type, mysql_params)
    get_db("""
    CREATE TABLE IF NOT EXISTS tiqué (
        ID_tiqué INTEGER PRIMARY KEY AUTOINCREMENT,
        ID_user TEXT NOT NULL,
        titre TEXT NOT NULL,
        description TEXT NOT NULL,
        gravite INTEGER CHECK (gravite BETWEEN 1 AND 5),
        date_open TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        date_close TIMESTAMP NULL,
        tag TEXT,
        open INTEGER DEFAULT 1 CHECK (open IN (0,1)),
        ID_technicien TEXT,
        priorite INTEGER DEFAULT 3 CHECK (priorite BETWEEN 1 AND 5),
        parent_ID_tiqué INTEGER NULL,
        FOREIGN KEY (parent_ID_tiqué) REFERENCES tiqué(ID_tiqué) ON DELETE CASCADE
    )
    """)
    
    # Index pour améliorer les performances
    get_db("CREATE INDEX IF NOT EXISTS idx_ticket_user ON tiqué(ID_user)")
    get_db("CREATE INDEX IF NOT EXISTS idx_ticket_tech ON tiqué(ID_technicien)")
    get_db("CREATE INDEX IF NOT EXISTS idx_ticket_open ON tiqué(open)")
    get_db("CREATE INDEX IF NOT EXISTS idx_ticket_date ON tiqué(date_open)")

def migrate_comments():
    """Migration des commentaires vers une table dédiée"""
    get_db("""
    CREATE TABLE IF NOT EXISTS ticket_comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id INTEGER NOT NULL,
        user_id TEXT NOT NULL,
        content TEXT NOT NULL,
        gravite INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (ticket_id) REFERENCES tiqué(ID_tiqué) ON DELETE CASCADE
    )
    """)
    
    # Index pour les commentaires
    get_db("CREATE INDEX IF NOT EXISTS idx_comment_ticket ON ticket_comments(ticket_id)")
    get_db("CREATE INDEX IF NOT EXISTS idx_comment_user ON ticket_comments(user_id)")

if __name__ == '__main__':
    print("=== CRÉATION DES TABLES TICKETS ===")
    try:
        create_tickets_table()
        print("Table tickets créée avec succès")
        
        migrate_comments()
        print("Table commentaires créée avec succès")
        
    except Exception as e:
        print(f"Erreur lors de la création des tables: {e}")
    print("=== FIN DE LA CRÉATION DES TABLES ===")
