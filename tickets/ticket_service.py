import string
import secrets
import datetime
import uuid
import logging
from utils.db_manager import get_db, log_activity
from flask import session

# Récupérer le logger de l'application
logger = logging.getLogger('glpibis')

def generate_ticket_id(length=16):
    """
    Generates a unique ID for a ticket
    """
    valid_chars = string.ascii_letters
    return ''.join(secrets.choice(valid_chars) for _ in range(length))

def create_ticket(user_id, titre, description, gravite, tags):
    """
    Creates a new ticket in the database
    
    Args:
        user_id (str): ID of the user creating the ticket
        titre (str): Ticket title
        description (str): Detailed description of the problem
        gravite (str/int): Ticket severity level
        tags (str): Tags or categories associated with the ticket
    
    Returns:
        int: Created ticket ID
    """
    import sqlite3
    
    # S'assurer que user_id est une chaîne
    user_id = str(user_id)
    
    # Validation des entrées
    if not titre or not description:
        raise ValueError("Le titre et la description sont obligatoires")
        
    # Conversion sécurisée de la gravité en entier entre 1 et 5
    try:
        gravite_int = max(1, min(5, int(gravite)))
    except (ValueError, TypeError):
        gravite_int = 3  # Valeur par défaut
    
    # S'assurer que tags est une chaîne
    tags = str(tags or "")
    
    current_date = str(datetime.date.today())
    
    # Utiliser une connexion directe à SQLite pour un meilleur contrôle des erreurs
    try:
        # Obtenir une connexion directe à la base de données
        conn = get_db('connect')
        cursor = conn.cursor()
        
        # Insérer le ticket en laissant SQLite générer l'ID automatiquement
        # Ne pas spécifier ID_tiqué pour qu'il soit auto-incrémenté
        cursor.execute("""
            INSERT INTO tiqué (ID_user, titre, date_open, description, gravite, tag, open)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, titre, current_date, description, gravite_int, tags, 1))
        
        # Récupérer l'ID généré automatiquement
        ticket_id = cursor.lastrowid
        
        # Valider la transaction
        conn.commit()
        
        # Création d'une table pour les commentaires du ticket
        # Utiliser un nom de table avec préfixe pour éviter les conflits
        comment_table_name = f"comments_ticket_{ticket_id}"
        cursor.execute(f"""CREATE TABLE IF NOT EXISTS {comment_table_name} (
            ID_user TEXT, 
            date TEXT, 
            hour TEXT, 
            commenter TEXT,
            gravité INTEGER DEFAULT 0
        )""")
        
        conn.commit()
    except sqlite3.Error as e:
        # Journaliser l'erreur avec les détails
        print(f"Erreur SQLite lors de l'insertion du ticket: {e}")
        print(f"Valeurs: ID_user={user_id}, titre={titre}, date_open={current_date}, description={len(description)} chars, gravite={gravite_int}, tag={tags}, open=1")
        
        # Vérifier l'existence et la structure de la table
        try:
            cursor.execute("PRAGMA table_info(tiqué)")
            table_structure = cursor.fetchall()
            print("Structure de la table tiqué:", table_structure)
        except Exception as ex:
            print(f"Impossible de récupérer la structure de la table: {ex}")
        
        # Propager l'exception
        raise
    
    # Mise à jour des statistiques de l'utilisateur
    update_user_stats(user_id, "tiqué_créer", str(ticket_id))
    
    return ticket_id

def create_subticket(user_id, parent_ticket_id, titre, description, gravite, tags):
    """
    Crée un sous-ticket lié à un ticket parent dans la base de données

    Args:
        user_id (str): ID de l'utilisateur créant le sous-ticket
        parent_ticket_id (str): ID du ticket parent
        titre (str): Titre du sous-ticket
        description (str): Description détaillée du sous-ticket
        gravite (str/int): Niveau de gravité du sous-ticket
        tags (str): Tags ou catégories associés au sous-ticket

    Returns:
        str: ID du sous-ticket créé
    """
    subticket_id = generate_ticket_id()
    
    # Assurer que les variables ont le bon type
    user_id = str(user_id)
    parent_ticket_id = str(parent_ticket_id)
    titre = str(titre)
    description = str(description)
    
    # Conversion sécurisée de la gravité en entier
    try:
        gravite_int = int(gravite)
    except (ValueError, TypeError):
        gravite_int = 3  # Valeur par défaut si la conversion échoue
    
    # S'assurer que tags est une chaîne
    if tags is None:
        tags = ""
    else:
        tags = str(tags)
    
    current_date = str(datetime.date.today())

    # Insertion du sous-ticket avec des points d'interrogation comme paramètres
    try:
        get_db("""
            INSERT INTO tiqué (ID_tiqué, ID_user, parent_ID_tiqué, date_open, titre, description, gravite, tag, open)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (subticket_id, user_id, parent_ticket_id, current_date, titre, description, gravite_int, tags, 1))
    except Exception as e:
        print(f"Erreur lors de l'insertion du sous-ticket: {e}")
        # Afficher les valeurs pour le débogage
        print(f"Valeurs: ID_tiqué={subticket_id}, ID_user={user_id}, parent_ID_tiqué={parent_ticket_id}, date_open={current_date}, titre={titre}, description={len(description)} chars, gravite={gravite_int}, tag={tags}, open=1")
        raise

    # Création d'une table pour les commentaires du sous-ticket
    get_db(f"""CREATE TABLE IF NOT EXISTS {subticket_id} (
        ID_user VARCHAR(255), 
        date TEXT, 
        hour TEXT, 
        commenter TEXT,
        gravité INTEGER DEFAULT 0
    )""")

    # Mise à jour des statistiques de l'utilisateur
    update_user_stats(user_id, "tiqué_créer", subticket_id)

    return subticket_id

def list_tickets(filter_value=None):
    """
    Liste tous les tickets selon un filtre optionnel
    
    Args:
        filter_value (str, optional): Valeur pour filtrer les tickets
            - 'all': tous les tickets
            - 'open': tickets ouverts
            - 'closed': tickets fermés
            - 'my': tickets créés par l'utilisateur actuel
            - 'software_X': tickets liés au logiciel X
            - 'hardware_X': tickets liés au matériel X
            - 'gravity_X': tickets avec gravité X
            - autre: filtrage par tag
    
    Returns:
        list: Liste des tickets correspondant au filtre
    """
    user_id = session.get('user_id')
    query = "SELECT * FROM tiqué "
    params = []
    
    if filter_value == "all" or not filter_value:
        # Pas de condition WHERE, récupérer tous les tickets
        pass
    elif filter_value == "open":
        query += "WHERE open = 1 "
    elif filter_value == "closed":
        query += "WHERE open = 0 "
    elif filter_value == "my" and user_id:
        query += "WHERE ID_user = ? "
        params.append(user_id)
    elif filter_value and filter_value.startswith("gravity_"):
        # Extraire le niveau de gravité du filtre (gravity_1, gravity_2, etc.)
        try:
            gravity_level = int(filter_value.split("_")[1])
            query += "WHERE gravite = ? "
            params.append(gravity_level)
        except (IndexError, ValueError):
            # En cas d'erreur de format, ne pas appliquer de filtre
            pass
    elif filter_value and (filter_value.startswith("software_") or filter_value.startswith("hardware_")):
        # Extraire la catégorie (remplacer les underscores par des espaces)
        category_type = filter_value.split("_")[0]  # software ou hardware
        category = filter_value[len(category_type)+1:].replace("_", " ")
        
        # Filtrer par tag contenant la catégorie (recherche partielle)
        query += "WHERE tag LIKE ? "
        params.append("%" + category + "%")
    elif filter_value:
        # Filtrer par tag (recherche exacte ou partielle)
        query += "WHERE tag LIKE ? "
        params.append("%" + filter_value + "%")
    
    # Ajouter l'ordre de tri
    query += "ORDER BY date_open DESC"
    
    # Exécuter la requête avec les paramètres
    tickets = get_db(query, tuple(params)) if params else get_db(query)
    
    # Formater les tickets avec les noms d'utilisateurs
    formatted_tickets = []
    for ticket in tickets:
        try:
            user_info = get_db("SELECT name FROM USEUR WHERE ID = ?", (ticket[1],))
            user_name = user_info[0][0] if user_info else "Utilisateur inconnu"
            
            ticket_data = list(ticket)
            ticket_data.append(user_name)  # Ajouter le nom de l'utilisateur
            formatted_tickets.append(tuple(ticket_data))
        except Exception as e:
            print(f"Erreur lors du formatage du ticket {ticket[0]}: {e}")
            # Ajouter quand même le ticket sans modification
            formatted_tickets.append(ticket)
    
    return formatted_tickets

def get_ticket_info(ticket_id):
    """
    Récupère les informations d'un ticket spécifique
    
    Args:
        ticket_id (str): ID du ticket
    
    Returns:
        tuple: Informations du ticket ou None si non trouvé
    """
    try:
        print(f"DEBUG - get_ticket_info: Début de la récupération des informations pour le ticket {ticket_id}")
        
        # Requête modifiée pour inclure ID_technicien et nom du technicien assigné avec colonnes explicites
        query = """
            SELECT t.ID_tiqué, t.ID_user, t.titre, t.date_open, t.description, t.gravite, t.tag, t.open, t.date_close,
                   u.name as user_name, tech.ID as tech_id, tech.name as tech_name
            FROM tiqué t
            LEFT JOIN USEUR u ON t.ID_user = u.ID
            LEFT JOIN USEUR tech ON t.ID_technicien = tech.ID
            WHERE t.ID_tiqué = ?
        """
        print(f"DEBUG - get_ticket_info: Exécution de la requête: {query} avec paramètre: {ticket_id}")
        
        tickets = get_db(query, (ticket_id,))
        print(f"DEBUG - get_ticket_info: Résultat de la requête: {tickets}")
        
        if not tickets:
            print(f"DEBUG - get_ticket_info: Aucun ticket trouvé avec ID {ticket_id}")
            return None
        
        ticket_data = list(tickets[0])
        
        print(f"DEBUG - get_ticket_info: Ticket formaté avec succès: {ticket_data}")
        return tuple(ticket_data)
    except Exception as e:
        print(f"DEBUG - get_ticket_info: ERREUR lors de la récupération des informations du ticket {ticket_id}: {str(e)}")
        import traceback
        print(f"DEBUG - get_ticket_info: Traceback complet: {traceback.format_exc()}")
        return None

def get_ticket_comments(ticket_id):
    """
    Récupère tous les commentaires d'un ticket
    
    Args:
        ticket_id (str): ID du ticket
    
    Returns:
        list: Liste des commentaires du ticket
    """
    try:
        # Nom de la table de commentaires
        comment_table_name = f"comments_ticket_{ticket_id}"
        
        # Vérifier si la table existe en utilisant PRAGMA table_info (compatible SQLite)
        check_query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        tables = get_db(check_query, (comment_table_name,))
        
        if not tables:
            return []
        
        # Récupérer les commentaires en utilisant une connexion directe pour éviter les problèmes de formatage
        conn = get_db('connect')
        cursor = conn.cursor()
        query = f"SELECT * FROM {comment_table_name} ORDER BY date, hour"
        cursor.execute(query)
        comments = cursor.fetchall()
        return comments
    except Exception as e:
        print(f"Erreur lors de la récupération des commentaires pour le ticket {ticket_id}: {e}")
        return []

def add_comment(ticket_id, user_id, comment_text, gravite):
    """
    Ajoute un commentaire à un ticket
    
    Args:
        ticket_id (str): ID du ticket
        user_id (str): ID de l'utilisateur
        comment_text (str): Texte du commentaire
        gravite (str/int): Niveau de gravité du commentaire
    
    Returns:
        bool: True si le commentaire a été ajouté avec succès
    """
    try:
        # Vérifier si le ticket existe en utilisant des paramètres
        ticket = get_db("SELECT * FROM tiqué WHERE ID_tiqué = ?", (ticket_id,))
        if not ticket:
            raise ValueError(f"Le ticket {ticket_id} n'existe pas")
        
        # Conversion sécurisée de la gravité en entier
        try:
            gravite_int = int(gravite)
        except (ValueError, TypeError):
            gravite_int = 3  # Valeur par défaut si la conversion échoue
        
        # Construire le nom de la table des commentaires
        comment_table_name = f"comments_ticket_{ticket_id}"
        
        # Vérifier si la table existe
        check_query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        tables = get_db(check_query, (comment_table_name,))
        
        if not tables:
            # Créer la table de commentaires si elle n'existe pas
            create_table_query = f"""CREATE TABLE IF NOT EXISTS {comment_table_name} (
                ID_user TEXT, 
                date TEXT, 
                hour TEXT, 
                commenter TEXT,
                gravité INTEGER DEFAULT 0
            )"""
            get_db(create_table_query)
        
        # Ajouter le commentaire
        now = datetime.datetime.now()
        date_str = str(now.date())
        time_str = now.time().strftime("%H:%M:%S")
        
        insert_query = f"""INSERT INTO {comment_table_name} 
                (ID_user, date, hour, commenter, gravité) 
                VALUES (?, ?, ?, ?, ?)"""
        
        get_db(insert_query, (user_id, date_str, time_str, comment_text, gravite_int))
        
        # Mise à jour des statistiques de l'utilisateur
        update_user_stats(user_id, "post_comm", ticket_id)
        
        return True
    except Exception as e:
        print(f"Erreur lors de l'ajout du commentaire au ticket {ticket_id}: {e}")
        return False

def close_ticket(ticket_id, user_id):
    """
    Ferme un ticket
    
    Args:
        ticket_id (str): ID du ticket à fermer
        user_id (str): ID de l'utilisateur fermant le ticket
    
    Returns:
        bool: True si le ticket a été fermé avec succès
        
    Raises:
        ValueError: Si le ticket n'existe pas ou si l'utilisateur n'a pas les droits
    """
    logger.info(f"Tentative de fermeture du ticket {ticket_id} par l'utilisateur {user_id}")
    
    # Vérifier si le ticket existe
    ticket = get_db("SELECT * FROM tiqué WHERE ID_tiqué = ?", (ticket_id,))
    if not ticket:
        logger.warning(f"Le ticket {ticket_id} n'existe pas")
        raise ValueError(f"Le ticket {ticket_id} n'existe pas")
    
    logger.debug(f"Ticket trouvé: {ticket}")
    
    # Vérifier si le ticket n'est pas déjà fermé
    if ticket[0][7] == 0:  # Indice 7 correspond à la colonne 'open'
        logger.warning(f"Le ticket {ticket_id} est déjà fermé")
        raise ValueError("Ce ticket est déjà fermé")
    
    # Construire le nom de la table de commentaires
    comment_table_name = f"comments_ticket_{ticket_id}"
    
    # Vérifier si l'utilisateur a participé au ticket
    check_query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
    tables = get_db(check_query, (comment_table_name,))
    
    user_participation = False
    if tables:
        # La table existe, vérifier si l'utilisateur a participé
        user_comments = get_db(f"SELECT * FROM {comment_table_name} WHERE ID_user = ?", (user_id,))
        user_participation = len(user_comments) > 0
        logger.debug(f"Participation de l'utilisateur via commentaires: {user_participation}")
    
    created_by_user = ticket[0][1] == user_id
    logger.debug(f"Ticket créé par l'utilisateur: {created_by_user}")
    
    if not (user_participation or created_by_user):
        logger.warning(f"L'utilisateur {user_id} n'a pas les droits pour fermer le ticket {ticket_id}")
        raise ValueError("Vous devez avoir participé au ticket pour pouvoir le fermer")
    
    # Fermer le ticket
    current_date = str(datetime.date.today())
    try:
        conn = get_db('connect')
        cursor = conn.cursor()
        cursor.execute("UPDATE tiqué SET open = 0, date_close = ? WHERE ID_tiqué = ?", 
                      (current_date, ticket_id))
        conn.commit()
        logger.info(f"Ticket {ticket_id} fermé avec succès")
        
        # Vérifier que la mise à jour a bien été effectuée
        updated_ticket = get_db("SELECT open FROM tiqué WHERE ID_tiqué = ?", (ticket_id,))
        if updated_ticket and updated_ticket[0][0] == 0:
            logger.info("Vérification réussie - le ticket est bien fermé")
            return True
        else:
            logger.error("Le ticket n'a pas été correctement fermé")
            raise ValueError("Erreur lors de la fermeture du ticket - la mise à jour n'a pas été effectuée")
            
    except Exception as e:
        logger.exception(f"Erreur lors de la fermeture du ticket: {str(e)}")
        raise ValueError(f"Erreur lors de la fermeture du ticket: {str(e)}")

def update_user_stats(user_id, stat_type, ticket_id):
    """
    Met à jour les statistiques d'un utilisateur
    
    Args:
        user_id (str): ID de l'utilisateur
        stat_type (str): Type de statistique à mettre à jour ('tiqué_créer' ou 'post_comm')
        ticket_id (str/int): ID du ticket concerné
    
    Returns:
        bool: True si les statistiques ont été mises à jour avec succès
    """
    # Assurer que les paramètres sont du bon type
    user_id = str(user_id) if user_id is not None else None
    ticket_id = str(ticket_id) if ticket_id is not None else None
    
    # Vérifier si l'utilisateur existe
    user = get_db("SELECT * FROM USEUR WHERE ID = ?", (user_id,))
    if not user:
        print(f"Avertissement: L'utilisateur {user_id} n'existe pas, impossible de mettre à jour les statistiques")
        return False
    
    try:
        # Récupérer les statistiques actuelles
        stats = get_db("SELECT * FROM state WHERE id_user = ?", (user_id,))
        
        if not stats:
            # Si l'utilisateur n'a pas d'entrée dans la table des statistiques, en créer une
            get_db("INSERT INTO state (id_user, tiqué_créer, tiqué_partisipé, comm) VALUES (?, 0, 0, 0)", 
                (user_id,))
            stats = [(user_id, 0, 0, 0)]
        
        # Mettre à jour les statistiques en fonction du type
        if stat_type == "tiqué_créer":
            tickets_created = int(stats[0][1]) + 1 if stats[0][1] is not None else 1
            get_db("UPDATE state SET tiqué_créer = ? WHERE id_user = ?", 
                (tickets_created, user_id))
        
        elif stat_type == "post_comm":
            # Vérifier si l'utilisateur a créé le ticket
            ticket = get_db("SELECT * FROM tiqué WHERE ID_tiqué = ?", (ticket_id,))
            is_creator = ticket and ticket[0][1] == user_id
            
            if not is_creator:
                # Incrémenter le nombre de tickets auxquels l'utilisateur a participé
                tickets_participated = int(stats[0][2]) + 1 if stats[0][2] is not None else 1
                get_db("UPDATE state SET tiqué_partisipé = ? WHERE id_user = ?", 
                    (tickets_participated, user_id))
            
            # Incrémenter le nombre de commentaires
            comments = int(stats[0][3]) + 1 if stats[0][3] is not None else 1
            get_db("UPDATE state SET comm = ? WHERE id_user = ?", 
                (comments, user_id))
        
        return True
    except Exception as e:
        print(f"Erreur lors de la mise à jour des statistiques: {e}")
        return False

def associate_hardware_to_ticket(ticket_id, hardware_id):
    """
    Associe un matériel à un ticket
    
    Args:
        ticket_id (str): ID du ticket
        hardware_id (int): ID du matériel
    
    Returns:
        bool: True si l'association a été créée avec succès
    """
    try:
        # Vérifier si le ticket existe
        ticket = get_db("SELECT * FROM tiqué WHERE ID_tiqué = ?", (ticket_id,))
        if not ticket:
            raise ValueError(f"Le ticket {ticket_id} n'existe pas")
        
        # Vérifier si le matériel existe
        hardware = get_db("SELECT * FROM materiel WHERE id = ?", (hardware_id,))
        if not hardware:
            raise ValueError(f"Le matériel avec ID {hardware_id} n'existe pas")
        
        # Vérifier si l'association existe déjà
        existing = get_db("SELECT * FROM ticket_materiel WHERE id_ticket = ? AND id_materiel = ?", 
                        (ticket_id, hardware_id))
        if existing:
            return True  # L'association existe déjà
        
        # Créer l'association
        get_db("""
            INSERT INTO ticket_materiel (id_ticket, id_materiel, date_association)
            VALUES (?, ?, ?)
        """, (ticket_id, hardware_id, str(datetime.date.today())))
        
        return True
    except Exception as e:
        print(f"Erreur lors de l'association du matériel au ticket: {e}")
        return False

def disassociate_hardware_from_ticket(ticket_id, hardware_id):
    """
    Supprime l'association entre un matériel et un ticket
    
    Args:
        ticket_id (str): ID du ticket
        hardware_id (int): ID du matériel
    
    Returns:
        bool: True si l'association a été supprimée avec succès
    """
    # Supprimer l'association
    get_db("""
        DELETE FROM ticket_materiel
        WHERE id_ticket = ? AND id_materiel = ?
    """, (ticket_id, hardware_id))
    
    return True

def get_associated_hardware(ticket_id):
    """
    Récupère la liste du matériel associé à un ticket
    
    Args:
        ticket_id (str): ID du ticket
    
    Returns:
        list: Liste des matériels associés au ticket
    """
    # Récupérer les IDs du matériel associé
    hardware_ids = get_db("""
        SELECT tm.id_materiel, m.nom, c.nom AS categorie, sc.nom AS sous_categorie, ssc.nom AS sous_sous_categorie
        FROM ticket_materiel tm
        JOIN materiel m ON tm.id_materiel = m.id
        LEFT JOIN categorie c ON m.categorie = c.id
        LEFT JOIN sous_categorie sc ON m.sous_categorie = sc.id
        LEFT JOIN sous_sous_categorie ssc ON m.sous_sous_categorie = ssc.id
        WHERE tm.id_ticket = ?
    """, (ticket_id,))
    
    return hardware_ids

def get_available_hardware():
    """
    Gets the list of all hardware available to be associated with a ticket.
    
    Returns:
        list: List of all available hardware
    """
    query = "SELECT m.id, m.nom, c.nom AS categorie, sc.nom AS sous_categorie, ssc.nom AS sous_sous_categorie FROM materiel m LEFT JOIN categorie c ON m.categorie = c.id LEFT JOIN sous_categorie sc ON m.sous_categorie = sc.id LEFT JOIN sous_sous_categorie ssc ON m.sous_sous_categorie = ssc.id"
    hardware = get_db(query)
    return hardware

# Import de la classe dans un module séparé
from .sous_ticket_service import SousTicketService