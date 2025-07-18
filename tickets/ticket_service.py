"""
Service de gestion des tickets
"""
import uuid
import datetime
import logging
from utils.db_manager import get_db, log_activity

logger = logging.getLogger('glpibis')

def create_ticket(user_id, titre, description, gravite=3, tags="", equipement_id=None, new_equipement=False, categorie=None):
    """
    Crée un nouveau ticket avec validation des données
    
    Args:
        user_id (str): ID de l'utilisateur créateur
        titre (str): Titre du ticket
        description (str): Description du problème
        gravite (int): Niveau de gravité (1-5)
        tags (str): Tags séparés par des virgules
    
    Returns:
        int: ID du ticket créé
    """
    try:
        # Validation des données
        if not titre or len(titre.strip()) < 3:
            raise ValueError("Le titre doit contenir au moins 3 caractères")
            
        if not description:
            raise ValueError("La description est obligatoire")
            
        if not 1 <= int(gravite) <= 5:
            raise ValueError("La gravité doit être entre 1 et 5")
            
        # Préparer les catégories
        cat_logicielle = cat_materielle = None
        if categorie:
            if categorie in ["outlook", "office", "windows", "antivirus", "browser"]:
                cat_logicielle = categorie
            elif categorie in ["computer", "printer", "phone", "network", "server"]:
                cat_materielle = categorie
        
        # Insérer le ticket
        result = get_db("""
            INSERT INTO tiqué (
                ID_user, titre, description, gravite, tag,
                date_open, open, equipement_id, new_equipement,
                categorie_logicielle, categorie_materielle
            ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?)
        """, (
            user_id, titre, description, int(gravite), tags,
            datetime.datetime.now(), equipement_id, new_equipement,
            cat_logicielle, cat_materielle
        ))
        
        # Récupérer l'ID du ticket créé
        ticket_id = get_db("SELECT last_insert_rowid()")[0][0]
        
        # Log de l'activité
        log_activity(user_id, 'create', 'ticket', f"Ticket créé: {titre}")
        
        logger.info(f"Ticket créé avec succès - ID: {ticket_id}, Titre: {titre}")
        return ticket_id
        
    except Exception as e:
        logger.error(f"Erreur lors de la création du ticket: {str(e)}")
        raise

def get_ticket_info(ticket_id):
    """
    Récupère les informations d'un ticket
    """    
    try:
        ticket = get_db("""
            SELECT * FROM tiqué t WHERE t.ID_tiqué = ?
        """, (ticket_id,))
        
        if ticket and len(ticket) > 0:
            ticket_data = ticket[0]
            # Convertir en dictionnaire avec les noms corrects
            return {
                'ID_tiqué': ticket_data[0],
                'ID_user': ticket_data[1],
                'titre': ticket_data[2],
                'date_open': ticket_data[3],
                'date_close': ticket_data[4],
                'ID_technicien': ticket_data[5],
                'description': ticket_data[6],
                'open': ticket_data[7],
                'tag': ticket_data[8],
                'gravite': ticket_data[9],
            }
        else:
            ticket = None
            logger.warning(f"Ticket non trouvé pour ID: {ticket_id}")
        return None
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du ticket: {str(e)}")
        raise

def close_ticket(ticket_id, user_id=None):
    """
    Ferme un ticket
    """
    try:
        get_db("""
            UPDATE tiqué 
            SET open = 0, date_close = ?
            WHERE ID_tiqué = ?
        """, (datetime.datetime.now(), ticket_id))
        
        if user_id:
            log_activity(user_id, 'close', 'ticket', f"Ticket {ticket_id} fermé")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la fermeture du ticket: {str(e)}")
        raise

def get_ticket_list(user_id=None, status=None, limit=10):
    """
    Récupère la liste des tickets avec informations détaillées
    """
    try:
        query = """
            SELECT t.ID_tiqué, t.titre, t.gravite, t.open, 
                   COALESCE(u1.name, 'Non assigné') as assignee,
                   t.date_open,
                   CASE 
                       WHEN t.open = 0 THEN 'Fermé'
                       WHEN t.gravite <= 2 THEN 'Urgent'
                       ELSE 'En cours'
                   END as statut,
                   CASE 
                       WHEN t.gravite <= 2 THEN 'danger'
                       WHEN t.gravite <= 4 THEN 'warning'
                       ELSE 'success'
                   END as priorite_class,
                   CASE 
                       WHEN t.open = 0 THEN 'success'
                       WHEN t.gravite <= 2 THEN 'danger'
                       ELSE 'primary'
                   END as statut_class
            FROM tiqué t
            LEFT JOIN USEUR u1 ON t.ID_technicien = u1.ID
        """
        params = []
        
        if user_id:
            query += " WHERE t.ID_user = ?"
            params.append(user_id)
        
        if status is not None:
            if 'WHERE' in query:
                query += " AND t.open = ?"
            else:
                query += " WHERE t.open = ?"
            params.append(status)
        
        query += " ORDER BY t.date_open DESC LIMIT ?"
        params.append(limit)

        tickets = get_db(query, tuple(params))
        
        # Formater les résultats
        formatted_tickets = []
        for ticket in tickets:
            formatted_tickets.append({
                'id': ticket[0],
                'titre': ticket[1],
                'priorite': f"Niveau {ticket[2]}",
                'statut': ticket[6],
                'assigne_a': ticket[4],
                'derniere_maj': ticket[5],
                'priorite_class': ticket[7],
                'statut_class': ticket[8]
            })
            
        return formatted_tickets
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la liste des tickets: {str(e)}")
        return []