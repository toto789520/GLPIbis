"""Script de migration des tables de tickets"""
import os
import json
from utils.db_manager import init_db_manager
from tickets.create_db import create_tickets_table, migrate_comments

def main():
    # Lecture de la configuration
    config_path = os.path.join('config', 'conf.conf')
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        config = {"db_type": "sqlite"}
    
    # Initialisation de la base de données
    db_type = config.get('db_type', 'sqlite')
    mysql_params = config.get('mysql', {}) if db_type == 'mysql' else None
    db_mgr = init_db_manager(db_type, mysql_params)
    
    if not db_mgr:
        raise RuntimeError("Impossible d'initialiser le gestionnaire de base de données")
    
    print("Création des tables des tickets...")
    create_tickets_table()
    print("Migration des commentaires...")
    migrate_comments()
    print("Migration terminée avec succès")

if __name__ == '__main__':
    main()
