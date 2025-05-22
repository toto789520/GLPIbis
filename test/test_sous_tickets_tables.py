"""
Script de test pour les tables de sous-tickets
"""
import os
import sys
import unittest
import sqlite3

# Ajout du répertoire parent au chemin pour les importations
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tickets.create_sous_tickets_tables import create_sous_tickets_tables
from utils.db_manager import get_db

class TestSousTicketsTables(unittest.TestCase):
    """Test de la création des tables pour les sous-tickets"""
    
    def test_create_tables(self):
        """Test si les tables sont correctement créées"""
        # Créer les tables
        result = create_sous_tickets_tables()
        self.assertTrue(result, "La création des tables a échoué")
        
        # Vérifier que les tables existent
        conn = get_db('connect')
        cursor = conn.cursor()
        
        # Vérifier si la colonne nombre_sous_tickets existe dans la table tiqué
        cursor.execute("PRAGMA table_info(tiqué)")
        columns = [column[1] for column in cursor.fetchall()]
        self.assertIn('nombre_sous_tickets', columns, 
                     "La colonne 'nombre_sous_tickets' n'existe pas dans la table tiqué")
        
        # Vérifier les tables créées
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]
        
        expected_tables = [
            'sous_tickets',
            'sous_tickets_historique',
            'sous_tickets_commentaires',
            'sous_tickets_dependances'
        ]
        
        for table in expected_tables:
            self.assertIn(table, tables, f"La table '{table}' n'existe pas")
        
        print("✅ Les tables de sous-tickets ont été correctement créées.")
        
    def test_insert_sous_ticket(self):
        """Test l'insertion d'un sous-ticket dans la table"""
        import uuid
        
        # Créer un ticket parent si nécessaire
        cursor = get_db('connect').cursor()
        cursor.execute("SELECT ID_tiqué FROM tiqué LIMIT 1")
        parent_ticket = cursor.fetchone()
        
        if not parent_ticket:
            print("Aucun ticket parent trouvé, création d'un ticket...")
            from tickets.ticket_service import create_ticket
            parent_id = create_ticket(
                "test_user", 
                "Ticket de test", 
                "Description du ticket de test", 
                3, 
                "test"
            )
            print(f"Ticket parent créé avec l'ID: {parent_id}")
            parent_ticket = [parent_id]
        
        parent_id = parent_ticket[0]
        sous_ticket_id = str(uuid.uuid4())
        
        try:
            get_db("""
                INSERT INTO sous_tickets 
                (id, parent_ticket_id, titre, description, priorite, createur_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (sous_ticket_id, parent_id, "Sous-ticket de test", "Description du sous-ticket de test", 3, "test_user"))
            
            # Vérifier que le sous-ticket a été inséré
            sous_ticket = get_db("SELECT * FROM sous_tickets WHERE id = ?", (sous_ticket_id,))
            self.assertTrue(sous_ticket, "Le sous-ticket n'a pas été inséré")
            
            print(f"✅ Sous-ticket créé avec succès: {sous_ticket_id}")
        except Exception as e:
            self.fail(f"Échec de l'insertion du sous-ticket: {e}")

if __name__ == "__main__":
    unittest.main()
