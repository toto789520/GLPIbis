#!/usr/bin/env python3
"""
Script de débogage pour la création de tickets
"""

import os
import sys

# Ajouter le répertoire racine au path Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.db_manager import init_db_manager, get_db, get_tables_list
from utils.logger import get_logger

def main():
    """Fonction principale de débogage"""
    logger = get_logger()
    
    print("=== DÉBOGAGE CRÉATION DE TICKETS ===")
    
    try:
        # 1. Initialiser la base de données
        print("1. Initialisation de la base de données...")
        db_manager = init_db_manager('sqlite')
        print("✓ Base de données initialisée")
        
        # 2. Lister les tables
        print("\n2. Tables disponibles:")
        tables = get_tables_list()
        for table in tables:
            if isinstance(table, (list, tuple)):
                print(f"  - {table[0]}")
            else:
                print(f"  - {table}")
        
        # 3. Vérifier la structure de la table tiqué
        print("\n3. Structure de la table 'tiqué':")
        try:
            columns = get_db("PRAGMA table_info(tiqué)")
            if columns:
                for col in columns:
                    if isinstance(col, (list, tuple)) and len(col) >= 3:
                        print(f"  - {col[1]} ({col[2]}) - NOT NULL: {col[3]}")
                    else:
                        print(f"  - {col}")
            else:
                print("  ✗ Impossible de récupérer les colonnes")
        except Exception as e:
            print(f"  ✗ Erreur: {e}")
        
        # 4. Tester une insertion simple
        print("\n4. Test d'insertion de ticket...")
        test_user = "debug@test.com"
        
        # Créer l'utilisateur de test s'il n'existe pas
        existing_user = get_db("SELECT ID FROM USEUR WHERE ID = ?", (test_user,))
        if not existing_user or len(existing_user) == 0:
            print("  Création de l'utilisateur de test...")
            result = get_db("""
                INSERT INTO USEUR (ID, name, email, password, role)
                VALUES (?, ?, ?, ?, ?)
            """, (test_user, "Debug User", test_user, "debug123", "user"))
            if result:
                print("  ✓ Utilisateur créé")
            else:
                print("  ✗ Échec création utilisateur")
                return
        
        # Insérer un ticket de test
        from datetime import datetime
        
        insert_result = get_db("""
            INSERT INTO tiqué (ID_user, titre, description, gravite, tag, date_open, open)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (test_user, "Ticket Debug", "Test de débogage", 3, "debug", 
              datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 1))
        
        if insert_result:
            print("  ✓ Ticket inséré avec succès")
            
            # Vérifier l'insertion
            tickets = get_db("""
                SELECT ID_tiqué, titre, description, gravite, date_open, open
                FROM tiqué 
                WHERE ID_user = ? 
                ORDER BY date_open DESC
                LIMIT 1
            """, (test_user,))
            
            if tickets and len(tickets) > 0:
                ticket = tickets[0]
                print(f"  ✓ Ticket récupéré: ID={ticket[0]}, Titre='{ticket[1]}'")
            else:
                print("  ✗ Ticket non trouvé après insertion")
        else:
            print("  ✗ Échec de l'insertion du ticket")
        
        # 5. Compter les tickets
        print("\n5. Nombre total de tickets:")
        count_result = get_db("SELECT COUNT(*) FROM tiqué")
        if count_result and len(count_result) > 0:
            count = count_result[0][0] if isinstance(count_result[0], (list, tuple)) else count_result[0]
            print(f"  Total: {count} tickets")
        
        print("✓ Débogage terminé avec succès")
        
    except Exception as e:
        print(f"✗ Erreur pendant le débogage: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()