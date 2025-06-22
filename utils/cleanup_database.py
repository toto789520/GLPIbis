#!/usr/bin/env python3
"""
Script pour nettoyer et consolider les bases de données.
Utilise uniquement glpibis.db et supprime les autres fichiers de base de données.
"""

import os
import shutil
import sqlite3
from datetime import datetime

def cleanup_databases():
    """Nettoie et consolide les bases de données"""
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_db = os.path.join(project_root, 'glpibis.db')
    
    # Liste des fichiers de base de données à supprimer
    db_files_to_remove = [
        'db',
        'data', 
        'database.sqlite',
        'glpi.db',
        'app.db'
    ]
    
    print(f"Répertoire du projet: {project_root}")
    print(f"Base de données cible: {target_db}")
    
    # Créer une sauvegarde de glpibis.db s'il existe
    if os.path.exists(target_db):
        backup_name = f"glpibis_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        backup_path = os.path.join(project_root, backup_name)
        shutil.copy2(target_db, backup_path)
        print(f"Sauvegarde créée: {backup_name}")
    
    # Supprimer les autres fichiers de base de données
    removed_files = []
    for db_file in db_files_to_remove:
        db_path = os.path.join(project_root, db_file)
        if os.path.exists(db_path):
            try:
                if os.path.isfile(db_path):
                    os.remove(db_path)
                    removed_files.append(db_file)
                    print(f"Fichier supprimé: {db_file}")
                elif os.path.isdir(db_path):
                    # Si c'est un répertoire, le supprimer aussi
                    shutil.rmtree(db_path)
                    removed_files.append(db_file)
                    print(f"Répertoire supprimé: {db_file}")
            except Exception as e:
                print(f"Erreur lors de la suppression de {db_file}: {e}")
    
    # Vérifier que glpibis.db existe et est fonctionnel
    try:
        if not os.path.exists(target_db):
            print("Création de glpibis.db...")
            # Créer la base de données vide
            conn = sqlite3.connect(target_db)
            conn.execute("PRAGMA foreign_keys = ON")
            conn.close()
        
        # Tester la connexion
        conn = sqlite3.connect(target_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        conn.close()
        
        print(f"Base de données glpibis.db opérationnelle avec {len(tables)} tables")
        
    except Exception as e:
        print(f"Erreur avec glpibis.db: {e}")
        return False
    
    print("\n=== NETTOYAGE TERMINÉ ===")
    print(f"Fichiers supprimés: {', '.join(removed_files) if removed_files else 'Aucun'}")
    print(f"Base de données active: glpibis.db")
    
    return True

def consolidate_user_data():
    """Consolide les données utilisateur si plusieurs bases existaient"""
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    target_db = os.path.join(project_root, 'glpibis.db')
    
    try:
        conn = sqlite3.connect(target_db)
        cursor = conn.cursor()
        
        # Vérifier s'il y a des utilisateurs en double
        cursor.execute("""
            SELECT ID, COUNT(*) as count 
            FROM USEUR 
            GROUP BY email 
            HAVING COUNT(*) > 1
        """)
        
        duplicates = cursor.fetchall()
        
        if duplicates:
            print(f"\n{len(duplicates)} utilisateurs en double détectés")
            for user_id, count in duplicates:
                print(f"- Utilisateur {user_id}: {count} entrées")
            
            # Pour cet exemple, on garde le premier utilisateur de chaque email
            cursor.execute("""
                DELETE FROM USEUR 
                WHERE rowid NOT IN (
                    SELECT MIN(rowid) 
                    FROM USEUR 
                    GROUP BY email
                )
            """)
            
            print("Doublons supprimés")
        else:
            print("Aucun doublon détecté")
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"Erreur lors de la consolidation: {e}")

if __name__ == "__main__":
    print("=== NETTOYAGE DES BASES DE DONNÉES ===")
    
    if cleanup_databases():
        consolidate_user_data()
        print("\nNettoyage terminé avec succès!")
        print("Vous pouvez maintenant relancer l'application.")
    else:
        print("\nErreur lors du nettoyage.")