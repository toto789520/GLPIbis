#!/usr/bin/env python3
"""
Script pour migrer et consolider les données des multiples bases de données vers glpibis.db
"""

import os
import sqlite3
import shutil
from datetime import datetime

def migrate_databases():
    """Migre toutes les données vers glpibis.db"""
    
    project_root = os.getcwd()
    target_db = os.path.join(project_root, 'glpibis.db')
    
    # Créer une sauvegarde de glpibis.db s'il existe
    if os.path.exists(target_db):
        backup_name = f"glpibis_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        backup_path = os.path.join(project_root, backup_name)
        shutil.copy2(target_db, backup_path)
        print(f"Sauvegarde créée: {backup_name}")
    
    # Bases de données sources possibles
    source_dbs = []
    possible_dbs = ['db', 'data', 'database.sqlite', 'glpi.db', 'app.db']
    
    for db_name in possible_dbs:
        db_path = os.path.join(project_root, db_name)
        
        # Vérifier s'il s'agit d'un fichier SQLite
        if os.path.isfile(db_path):
            try:
                # Tester si c'est une base SQLite valide
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                if tables:
                    source_dbs.append((db_name, db_path, [t[0] for t in tables]))
                    print(f"Base de données trouvée: {db_name} ({len(tables)} tables)")
                conn.close()
            except:
                print(f"Fichier ignoré (pas une base SQLite): {db_name}")
        elif os.path.isdir(db_path):
            print(f"Répertoire ignoré: {db_name}")
    
    if not source_dbs:
        print("Aucune base de données source trouvée")
        return False
    
    # Créer ou ouvrir glpibis.db
    target_conn = sqlite3.connect(target_db)
    target_cursor = target_conn.cursor()
    
    # Activer les clés étrangères
    target_cursor.execute("PRAGMA foreign_keys = ON")
    
    # Structure des tables principales
    table_schemas = {
        'USEUR': '''
            CREATE TABLE IF NOT EXISTS USEUR (
                ID TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                age INTEGER,
                tel TEXT,
                password TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                role TEXT DEFAULT 'user'
            )
        ''',
        'tiqué': '''
            CREATE TABLE IF NOT EXISTS tiqué (
                ID_tiqué INTEGER PRIMARY KEY AUTOINCREMENT,
                ID_user TEXT NOT NULL,
                titre TEXT NOT NULL,
                date_open TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                date_close TIMESTAMP,
                ID_technicien TEXT,
                description TEXT,
                open INTEGER DEFAULT 1,
                tag TEXT,
                gravite INTEGER DEFAULT 1,
                FOREIGN KEY (ID_user) REFERENCES USEUR(ID),
                FOREIGN KEY (ID_technicien) REFERENCES USEUR(ID)
            )
        ''',
        'sessions': '''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                token TEXT UNIQUE NOT NULL,
                creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expiry_date TIMESTAMP NOT NULL,
                FOREIGN KEY (user_id) REFERENCES USEUR(ID)
            )
        '''
    }
    
    # Créer les tables dans la base cible
    for table_name, schema in table_schemas.items():
        target_cursor.execute(schema)
        print(f"Table {table_name} créée/vérifiée")
    
    # Migrer les données
    migrated_users = set()
    migrated_tickets = []
    
    for db_name, db_path, tables in source_dbs:
        print(f"\nMigration depuis {db_name}...")
        source_conn = sqlite3.connect(db_path)
        source_cursor = source_conn.cursor()
        
        # Migrer les utilisateurs
        if 'USEUR' in tables:
            source_cursor.execute("SELECT * FROM USEUR")
            users = source_cursor.fetchall()
            
            # Obtenir les noms des colonnes
            source_cursor.execute("PRAGMA table_info(USEUR)")
            columns_info = source_cursor.fetchall()
            column_names = [col[1] for col in columns_info]
            
            for user in users:
                user_dict = dict(zip(column_names, user))
                user_id = user_dict.get('ID')
                
                if user_id not in migrated_users:
                    # Insérer l'utilisateur
                    try:
                        # S'assurer que les champs obligatoires existent
                        if not user_dict.get('password'):
                            user_dict['password'] = 'password_temp'
                        if not user_dict.get('email'):
                            user_dict['email'] = f"{user_id}@example.com"
                        
                        target_cursor.execute('''
                            INSERT OR IGNORE INTO USEUR (ID, name, age, tel, password, email, creation_date, role)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            user_dict.get('ID'),
                            user_dict.get('name', 'Utilisateur'),
                            user_dict.get('age'),
                            user_dict.get('tel'),
                            user_dict.get('password', 'password_temp'),
                            user_dict.get('email', f"{user_id}@example.com"),
                            user_dict.get('creation_date'),
                            user_dict.get('role', 'user')
                        ))
                        migrated_users.add(user_id)
                        print(f"  Utilisateur migré: {user_dict.get('name', user_id)}")
                    except Exception as e:
                        print(f"  Erreur migration utilisateur {user_id}: {e}")
        
        # Migrer les tickets
        if 'tiqué' in tables:
            source_cursor.execute("SELECT * FROM tiqué")
            tickets = source_cursor.fetchall()
            
            # Obtenir les noms des colonnes
            source_cursor.execute("PRAGMA table_info(tiqué)")
            columns_info = source_cursor.fetchall()
            column_names = [col[1] for col in columns_info]
            
            for ticket in tickets:
                ticket_dict = dict(zip(column_names, ticket))
                
                try:
                    target_cursor.execute('''
                        INSERT INTO tiqué (ID_user, titre, date_open, date_close, ID_technicien, description, open, tag, gravite)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        ticket_dict.get('ID_user'),
                        ticket_dict.get('titre', 'Ticket sans titre'),
                        ticket_dict.get('date_open'),
                        ticket_dict.get('date_close'),
                        ticket_dict.get('ID_technicien'),
                        ticket_dict.get('description', ticket_dict.get('descriptio', '')),
                        ticket_dict.get('open', 1),
                        ticket_dict.get('tag'),
                        ticket_dict.get('gravite', 1)
                    ))
                    migrated_tickets.append(ticket_dict.get('titre', 'Sans titre'))
                    print(f"  Ticket migré: {ticket_dict.get('titre', 'Sans titre')}")
                except Exception as e:
                    print(f"  Erreur migration ticket: {e}")
        
        source_conn.close()
    
    # Sauvegarder les modifications
    target_conn.commit()
    target_conn.close()
    
    print(f"\n=== MIGRATION TERMINÉE ===")
    print(f"Utilisateurs migrés: {len(migrated_users)}")
    print(f"Tickets migrés: {len(migrated_tickets)}")
    print(f"Base de données consolidée: glpibis.db")
    
    return True

def cleanup_old_files():
    """Supprime les anciennes bases de données après migration"""
    project_root = os.getcwd()
    old_files = ['db', 'data', 'database.sqlite', 'glpi.db', 'app.db']
    
    print("\nSuppression des anciens fichiers...")
    for filename in old_files:
        filepath = os.path.join(project_root, filename)
        if os.path.exists(filepath):
            try:
                if os.path.isfile(filepath):
                    os.remove(filepath)
                    print(f"Fichier supprimé: {filename}")
                elif os.path.isdir(filepath):
                    shutil.rmtree(filepath)
                    print(f"Répertoire supprimé: {filename}")
            except Exception as e:
                print(f"Erreur suppression {filename}: {e}")

if __name__ == "__main__":
    print("=== MIGRATION ET CONSOLIDATION DES BASES DE DONNÉES ===")
    print("Ce script va consolider toutes vos bases de données en une seule: glpibis.db")
    
    response = input("\nContinuer? (o/n): ").lower()
    if response in ['o', 'oui', 'y', 'yes']:
        if migrate_databases():
            response = input("\nSupprimer les anciens fichiers? (o/n): ").lower()
            if response in ['o', 'oui', 'y', 'yes']:
                cleanup_old_files()
            print("\nMigration terminée! Vous pouvez maintenant relancer l'application.")
        else:
            print("Erreur lors de la migration.")
    else:
        print("Migration annulée.")