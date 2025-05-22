import uuid
from utils.db_manager import get_db, log_activity

class SousTicketService:
    @staticmethod
    def creer_sous_ticket(parent_ticket_id, titre, description, priorite, createur_id, assigne_a=None):
        """
        Crée un nouveau sous-ticket
        """
        sous_ticket_id = str(uuid.uuid4())
        
        try:
            # Vérifier d'abord si la table existe
            check_query = "SELECT name FROM sqlite_master WHERE type='table' AND name='sous_tickets'"
            tables = get_db(check_query)
            
            if not tables:
                print("La table 'sous_tickets' n'existe pas encore. Création des tables requises...")
                # Importer et exécuter la fonction pour créer les tables
                from tickets.create_sous_tickets_tables import create_sous_tickets_tables
                create_sous_tickets_tables()
            
            # Vérifier si la colonne nombre_sous_tickets existe dans la table tiqué
            conn = get_db('connect')
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(tiqué)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'nombre_sous_tickets' not in columns:
                print("La colonne 'nombre_sous_tickets' n'existe pas. Exécution du script de création des tables...")
                from tickets.create_sous_tickets_tables import create_sous_tickets_tables
                create_sous_tickets_tables()
            
            # Insérer le sous-ticket
            get_db("""
                INSERT INTO sous_tickets 
                (id, parent_ticket_id, titre, description, priorite, createur_id, assigne_a)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (sous_ticket_id, parent_ticket_id, titre, description, priorite, createur_id, assigne_a))
            
            # Mettre à jour le compteur de sous-tickets
            get_db("""
                UPDATE tiqué 
                SET nombre_sous_tickets = nombre_sous_tickets + 1
                WHERE ID_tiqué = ?
            """, (parent_ticket_id,))
            
            # Enregistrer dans l'historique
            get_db("""
                INSERT INTO sous_tickets_historique 
                (sous_ticket_id, user_id, type_modification, nouvelle_valeur)
                VALUES (?, ?, 'creation', ?)
            """, (sous_ticket_id, createur_id, f"Création du sous-ticket: {titre}"))
            
            log_activity(createur_id, 'create', 'sous-ticket', 
                        f"Création du sous-ticket '{titre}' pour le ticket {parent_ticket_id}")
            
            return sous_ticket_id
        except Exception as e:
            print(f"Erreur lors de la création du sous-ticket: {e}")
            return None

    @staticmethod
    def ajouter_dependance(sous_ticket_id, depend_de_id, user_id):
        """
        Ajoute une dépendance entre deux sous-tickets
        """
        try:
            # Vérifier d'abord si la table existe
            check_query = "SELECT name FROM sqlite_master WHERE type='table' AND name='sous_tickets_dependances'"
            tables = get_db(check_query)
            
            if not tables:
                print("La table 'sous_tickets_dependances' n'existe pas encore. Création des tables requises...")
                from tickets.create_sous_tickets_tables import create_sous_tickets_tables
                create_sous_tickets_tables()
            
            get_db("""
                INSERT INTO sous_tickets_dependances (sous_ticket_id, depend_de_id)
                VALUES (?, ?)
            """, (sous_ticket_id, depend_de_id))
            
            log_activity(user_id, 'update', 'sous-ticket', 
                        f"Ajout d'une dépendance entre les sous-tickets {sous_ticket_id} et {depend_de_id}")
            
            return True
        except Exception as e:
            print(f"Erreur lors de l'ajout de la dépendance: {e}")
            return False

    @staticmethod
    def changer_statut(sous_ticket_id, nouveau_statut, user_id):
        """
        Change le statut d'un sous-ticket
        """
        try:
            # Récupérer l'ancien statut
            ancien_statut = get_db("""
                SELECT statut FROM sous_tickets WHERE id = ?
            """, (sous_ticket_id,))[0][0]
            
            # Mettre à jour le statut
            get_db("""
                UPDATE sous_tickets 
                SET statut = ?,
                    date_resolution = CASE 
                        WHEN ? IN ('resolu', 'ferme') THEN datetime('now')
                        ELSE NULL
                    END
                WHERE id = ?
            """, (nouveau_statut, nouveau_statut, sous_ticket_id))
            
            # Enregistrer dans l'historique
            get_db("""
                INSERT INTO sous_tickets_historique 
                (sous_ticket_id, user_id, type_modification, ancienne_valeur, nouvelle_valeur)
                VALUES (?, ?, 'statut', ?, ?)
            """, (sous_ticket_id, user_id, ancien_statut, nouveau_statut))
            
            log_activity(user_id, 'update', 'sous-ticket', 
                        f"Changement de statut du sous-ticket {sous_ticket_id} de {ancien_statut} à {nouveau_statut}")
            
            return True
        except Exception as e:
            print(f"Erreur lors du changement de statut: {e}")
            return False

    @staticmethod
    def assigner_sous_ticket(sous_ticket_id, assigne_a, assigne_par):
        """
        Assigne un sous-ticket à un utilisateur
        """
        try:
            # Récupérer l'ancienne assignation
            ancien_assigne = get_db("""
                SELECT assigne_a FROM sous_tickets WHERE id = ?
            """, (sous_ticket_id,))[0][0]
            
            # Mettre à jour l'assignation
            get_db("""
                UPDATE sous_tickets SET assigne_a = ? WHERE id = ?
            """, (assigne_a, sous_ticket_id))
            
            # Enregistrer dans l'historique
            get_db("""
                INSERT INTO sous_tickets_historique 
                (sous_ticket_id, user_id, type_modification, ancienne_valeur, nouvelle_valeur)
                VALUES (?, ?, 'assignation', ?, ?)
            """, (sous_ticket_id, assigne_par, ancien_assigne or 'Non assigné', assigne_a))
            
            log_activity(assigne_par, 'update', 'sous-ticket', 
                        f"Assignation du sous-ticket {sous_ticket_id} à l'utilisateur {assigne_a}")
            
            return True
        except Exception as e:
            print(f"Erreur lors de l'assignation: {e}")
            return False

    @staticmethod
    def ajouter_commentaire(sous_ticket_id, user_id, commentaire):
        """
        Ajoute un commentaire à un sous-ticket
        """
        try:
            # Vérifier d'abord si la table existe
            check_query = "SELECT name FROM sqlite_master WHERE type='table' AND name='sous_tickets_commentaires'"
            tables = get_db(check_query)
            
            if not tables:
                print("La table 'sous_tickets_commentaires' n'existe pas encore. Création des tables requises...")
                from tickets.create_sous_tickets_tables import create_sous_tickets_tables
                create_sous_tickets_tables()
            
            get_db("""
                INSERT INTO sous_tickets_commentaires 
                (sous_ticket_id, user_id, commentaire)
                VALUES (?, ?, ?)
            """, (sous_ticket_id, user_id, commentaire))
            
            log_activity(user_id, 'comment', 'sous-ticket', 
                        f"Ajout d'un commentaire au sous-ticket {sous_ticket_id}")
            
            return True
        except Exception as e:
            print(f"Erreur lors de l'ajout du commentaire: {e}")
            return False

    @staticmethod
    def get_sous_tickets(parent_ticket_id):
        """
        Récupère tous les sous-tickets d'un ticket parent
        """
        try:
            # Vérifier d'abord si la table existe
            check_query = "SELECT name FROM sqlite_master WHERE type='table' AND name='sous_tickets'"
            tables = get_db(check_query)
            
            if not tables:
                print("La table 'sous_tickets' n'existe pas encore. Création des tables requises...")
                # Importer et exécuter la fonction pour créer les tables
                from tickets.create_sous_tickets_tables import create_sous_tickets_tables
                create_sous_tickets_tables()
                return []  # Retourner une liste vide car la table vient d'être créée
            
            # Continuer avec la requête si la table existe
            sous_tickets = get_db("""
                SELECT st.*, u1.name as createur_name, u2.name as assigne_name
                FROM sous_tickets st
                LEFT JOIN USEUR u1 ON st.createur_id = u1.ID
                LEFT JOIN USEUR u2 ON st.assigne_a = u2.ID
                WHERE st.parent_ticket_id = ?
                ORDER BY st.date_creation DESC
            """, (parent_ticket_id,))
            
            # Formater les résultats
            formatted_tickets = []
            for st in sous_tickets:
                formatted_tickets.append({
                    'id': st[0],
                    'parent_ticket_id': st[1],
                    'titre': st[2],
                    'description': st[3],
                    'statut': st[4],
                    'priorite': st[5],
                    'assigne_a': st[6],
                    'date_creation': st[7],
                    'date_modification': st[8],
                    'date_resolution': st[9],
                    'createur_id': st[10],
                    'createur_name': st[11],
                    'assigne_name': st[12]
                })
            
            return formatted_tickets
        except Exception as e:
            print(f"Erreur lors de la récupération des sous-tickets: {e}")
            return []
