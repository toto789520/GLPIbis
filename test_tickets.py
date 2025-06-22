# filepath: c:\Users\opm85\OneDrive\Documents\GitHub\GLPIbis\test_tickets.py
"""
Script de test pour la création de tickets
"""
import os
import sys

# Ajouter le répertoire racine au path Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.db_manager import init_db_manager, get_db
from datetime import datetime

# Variable globale pour stocker le gestionnaire de BDD
db_manager = None

def initialize_database():
    """Initialise la base de données pour les tests"""
    global db_manager
    try:
        print("Initialisation de la base de données...")
        db_manager = init_db_manager('sqlite')
        print("Base de données initialisée avec succès")
        return True
    except Exception as e:
        print(f"✗ Erreur lors de l'initialisation: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ticket_creation():
    """Test de création d'un ticket"""
    try:
        
        # Créer un utilisateur de test si nécessaire
        test_user_id = "test@example.com"
        existing_user = get_db("SELECT ID FROM USEUR WHERE ID = ?", (test_user_id,))
        
        if not existing_user:
            print("Création d'un utilisateur de test...")
            get_db("""
                INSERT INTO USEUR (ID, name, email, password, role)
                VALUES (?, ?, ?, ?, ?)
            """, (test_user_id, "Test User", test_user_id, "test123", "user"))
            print("Utilisateur de test créé")
        
        # Tester la création d'un ticket
        print("Test de création de ticket...")
        titre = "Ticket de test"
        description = "Ceci est un ticket de test créé automatiquement"
        gravite = 3
        tag = "test"
        
        result = get_db("""
            INSERT INTO tiqué (ID_user, titre, description, gravite, tag, date_open, open)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        """, (test_user_id, titre, description, gravite, tag, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        
        if result:
            print("✓ Ticket créé avec succès")
              # Vérifier que le ticket a été créé
            tickets = get_db("""
                SELECT ID_tiqué, titre, description, gravite, date_open
                FROM tiqué 
                WHERE ID_user = ? 
                ORDER BY date_open DESC
                LIMIT 1
            """, (test_user_id,))
            
            if tickets and len(tickets) > 0:
                if isinstance(tickets, list):
                    ticket = tickets[0]
                    print(f"✓ Ticket trouvé: ID={ticket[0]}, Titre='{ticket[1]}'")
                else:
                    print(f"✓ Ticket trouvé mais structure inattendue: {tickets}")
                return True
            else:
                print("✗ Aucun ticket trouvé après création")
                return False
        else:
            print("✗ Échec de la création du ticket")
            return False
            
    except Exception as e:
        print(f"✗ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_structure():
    """Test de la structure de la base de données"""
    try:
        print("\n=== VÉRIFICATION DE LA STRUCTURE DE LA BASE DE DONNÉES ===")
        
        # S'assurer que db_manager est bien initialisé
        if db_manager is None:
            print("✗ Gestionnaire de base de données non initialisé")
            return False
        
        # Vérifier la table tiqué
        columns = get_db("PRAGMA table_info(tiqué)")
        if columns and isinstance(columns, list) and len(columns) > 0:
            print("Colonnes de la table tiqué:")
            for col in columns:
                if isinstance(col, (list, tuple)) and len(col) > 2:
                    print(f"  - {col[1]} ({col[2]})")
                else:
                    print(f"  - {col}")
        else:
            print("✗ Table tiqué non trouvée ou vide")
            return False
        
        # Vérifier la table USEUR
        user_columns = get_db("PRAGMA table_info(USEUR)")
        if user_columns and isinstance(user_columns, list) and len(user_columns) > 0:
            print("Colonnes de la table USEUR:")
            for col in user_columns:
                if isinstance(col, (list, tuple)) and len(col) > 2:
                    print(f"  - {col[1]} ({col[2]})")
                else:
                    print(f"  - {col}")
        else:
            print("✗ Table USEUR non trouvée ou vide")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Erreur lors de la vérification: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("=== TEST DE CRÉATION DE TICKETS ===")
    
    # Initialiser la base de données en premier
    if not initialize_database():
        print("✗ Impossible d'initialiser la base de données")
        print("=== FIN DES TESTS ===")
        exit(1)
    
    # Test de la structure
    if test_database_structure():
        print("✓ Structure de la base de données OK")
        
        # Test de création
        if test_ticket_creation():
            print("✓ Test de création de tickets réussi")
        else:
            print("✗ Test de création de tickets échoué")
    else:
        print("✗ Problème avec la structure de la base de données")
    
    print("=== FIN DES TESTS ===")