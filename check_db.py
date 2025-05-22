"""Script de vérification de la base de données"""
import os
import json
from utils.db_manager import init_db_manager, get_db

def main():
    # Initialisation
    db_mgr = init_db_manager()
    
    # Vérifier les tables
    tables = get_db("SELECT name FROM sqlite_master WHERE type='table'")
    print("\nTables dans la base de données:")
    for table in tables:
        print(f"- {table[0]}")
        # Afficher la structure de la table
        structure = get_db(f"PRAGMA table_info({table[0]})")
        for col in structure:
            print(f"  * {col[1]} ({col[2]})")
        print()

if __name__ == '__main__':
    main()
