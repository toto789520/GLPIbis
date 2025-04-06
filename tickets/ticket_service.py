import string
import secrets
import datetime
import uuid
from utils.db import get_db, log_activity
from flask import session

def generate_ticket_id(length=16):
    """
    Génère un ID unique pour un ticket
    """
    valid_chars = string.ascii_letters
    return ''.join(secrets.choice(valid_chars) for _ in range(length))

def create_ticket(user_id, titre, description, gravite, tags):
    """
    Crée un nouveau ticket dans la base de données
    
    Args:
        user_id (str): ID de l'utilisateur créant le ticket
        titre (str): Titre du ticket
        description (str): Description détaillée du problème
        gravite (str/int): Niveau de gravité du ticket
        tags (str): Tags ou catégories associés au ticket
    
    Returns:
        str: ID du ticket créé
    """
    ticket_id = generate_ticket_id()
    
    # Préparation des données
    data = {
        'ID_user': user_id,
        'ID_tiqué': ticket_id,
        'date_open': str(datetime.date.today()),
        'titre': titre,
        'descipition': description,
        'gravite': int(gravite),
        'tag': tags,
        'open': 1
    }
    
    # Insertion du ticket
    get_db("""
        INSERT INTO tiqué (ID_tiqué, ID_user, date_open, titre, descipition, gravite, tag, open)
        VALUES (%(ID_tiqué)s, %(ID_user)s, %(date_open)s, %(titre)s, %(descipition)s, %(gravite)s, %(tag)s, %(open)s)
    """, data)
    
    # Création d'une table pour les commentaires du ticket
    get_db(f"""CREATE TABLE IF NOT EXISTS {ticket_id} (
        ID_user VARCHAR(255), 
        date TEXT, 
        hour TEXT, 
        commenter TEXT,
        gravité INTEGER DEFAULT 0
    )""")
    
    # Mise à jour des statistiques de l'utilisateur
    update_user_stats(user_id, "tiqué_créer", ticket_id)
    
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

    # Préparation des données
    data = {
        'ID_user': user_id,
        'ID_tiqué': subticket_id,
        'parent_ID_tiqué': parent_ticket_id,
        'date_open': str(datetime.date.today()),
        'titre': titre,
        'descipition': description,
        'gravite': int(gravite),
        'tag': tags,
        'open': 1
    }

    # Insertion du sous-ticket
    get_db("""
        INSERT INTO tiqué (ID_tiqué, ID_user, parent_ID_tiqué, date_open, titre, descipition, gravite, tag, open)
        VALUES (%(ID_tiqué)s, %(ID_user)s, %(parent_ID_tiqué)s, %(date_open)s, %(titre)s, %(descipition)s, %(gravite)s, %(tag)s, %(open)s)
    """, data)

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
        query += "WHERE ID_user = %s "
        params.append(user_id)
    elif filter_value.startswith("gravity_"):
        # Extraire le niveau de gravité du filtre (gravity_1, gravity_2, etc.)
        try:
            gravity_level = int(filter_value.split("_")[1])
            query += "WHERE gravite = %s "
            params.append(gravity_level)
        except (IndexError, ValueError):
            # En cas d'erreur de format, ne pas appliquer de filtre
            pass
    elif filter_value.startswith("software_") or filter_value.startswith("hardware_"):
        # Extraire la catégorie (remplacer les underscores par des espaces)
        category_type = filter_value.split("_")[0]  # software ou hardware
        category = filter_value[len(category_type)+1:].replace("_", " ")
        
        # Filtrer par tag contenant la catégorie (recherche partielle)
        query += "WHERE tag LIKE %s "
        params.append(f"%{category}%")
    else:
        # Filtrer par tag (recherche exacte ou partielle)
        query += "WHERE tag LIKE %s "
        params.append(f"%{filter_value}%")
    
    # Ajouter l'ordre de tri
    query += "ORDER BY date_open DESC"
    
    # Exécuter la requête avec les paramètres
    tickets = get_db(query, tuple(params)) if params else get_db(query)
    
    # Formater les tickets avec les noms d'utilisateurs
    formatted_tickets = []
    for ticket in tickets:
        try:
            user_info = get_db("SELECT name FROM USEUR WHERE ID = %s", (ticket[1],))
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
    tickets = get_db(f"SELECT * FROM tiqué WHERE ID_tiqué = '{ticket_id}'")
    if not tickets:
        return None
    
    # Récupérer le nom de l'utilisateur
    user_id = tickets[0][1]
    user_info = get_db(f"SELECT name FROM USEUR WHERE ID = '{user_id}'")
    user_name = user_info[0][0] if user_info else "Utilisateur inconnu"
    
    # Ajouter le nom d'utilisateur aux infos du ticket
    ticket_data = list(tickets[0])
    ticket_data.append(user_name)
    
    return tuple(ticket_data)

def get_ticket_comments(ticket_id):
    """
    Récupère tous les commentaires d'un ticket
    
    Args:
        ticket_id (str): ID du ticket
    
    Returns:
        list: Liste des commentaires du ticket
    """
    try:
        # Vérifier si la table existe
        table_exists = get_db(f"SHOW TABLES LIKE '{ticket_id}'")
        if not table_exists:
            return []
        
        # Récupérer les commentaires
        comments = get_db(f"SELECT * FROM {ticket_id} ORDER BY date, hour")
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
    # Vérifier si le ticket existe
    ticket = get_db(f"SELECT * FROM tiqué WHERE ID_tiqué = '{ticket_id}'")
    if not ticket:
        raise ValueError(f"Le ticket {ticket_id} n'existe pas")
    
    # Vérifier si la table de commentaires existe
    table_exists = get_db(f"SHOW TABLES LIKE '{ticket_id}'")
    if not table_exists:
        get_db(f"""CREATE TABLE {ticket_id} (
            ID_user VARCHAR(255), 
            date TEXT, 
            hour TEXT, 
            commenter TEXT,
            gravité INTEGER DEFAULT 0
        )""")
    
    # Ajouter le commentaire
    now = datetime.datetime.now()
    data = {
        'ID_user': user_id,
        'date': str(now.date()),
        'hour': now.time().strftime("%H:%M:%S"),
        'commenter': comment_text,
        'gravité': int(gravite)
    }
    
    get_db(f"""INSERT INTO {ticket_id} 
            (ID_user, date, hour, commenter, gravité) 
            VALUES (%(ID_user)s, %(date)s, %(hour)s, %(commenter)s, %(gravité)s)""", 
            data)
    
    # Mise à jour des statistiques de l'utilisateur
    update_user_stats(user_id, "post_comm", ticket_id)
    
    return True

def close_ticket(ticket_id, user_id):
    """
    Ferme un ticket
    
    Args:
        ticket_id (str): ID du ticket à fermer
        user_id (str): ID de l'utilisateur fermant le ticket
    
    Returns:
        bool: True si le ticket a été fermé avec succès
    """
    # Vérifier si le ticket existe
    ticket = get_db(f"SELECT * FROM tiqué WHERE ID_tiqué = '{ticket_id}'")
    if not ticket:
        raise ValueError(f"Le ticket {ticket_id} n'existe pas")
    
    # Vérifier si l'utilisateur a participé au ticket
    user_participation = get_db(f"SELECT * FROM {ticket_id} WHERE ID_user = '{user_id}'")
    created_by_user = ticket[0][1] == user_id
    
    if not (user_participation or created_by_user):
        raise ValueError("Vous devez avoir participé au ticket pour pouvoir le fermer")
    
    # Fermer le ticket
    get_db("""UPDATE tiqué SET open = 0, date_close = %s WHERE ID_tiqué = %s""", 
           (str(datetime.date.today()), ticket_id))
    
    return True

def update_user_stats(user_id, stat_type, ticket_id):
    """
    Met à jour les statistiques d'un utilisateur
    
    Args:
        user_id (str): ID de l'utilisateur
        stat_type (str): Type de statistique à mettre à jour ('tiqué_créer' ou 'post_comm')
        ticket_id (str): ID du ticket concerné
    
    Returns:
        bool: True si les statistiques ont été mises à jour avec succès
    """
    # Vérifier si l'utilisateur existe
    user = get_db("SELECT * FROM USEUR WHERE ID = %s", (user_id,))
    if not user:
        raise ValueError(f"L'utilisateur {user_id} n'existe pas")
    
    # Récupérer les statistiques actuelles
    stats = get_db("SELECT * FROM state WHERE id_user = %s", (user_id,))
    
    if not stats:
        # Si l'utilisateur n'a pas d'entrée dans la table des statistiques, en créer une
        get_db("INSERT INTO state (id_user, tiqué_créer, tiqué_partisipé, comm) VALUES (%s, 0, 0, 0)", 
               (user_id,))
        stats = [(user_id, 0, 0, 0)]
    
    # Mettre à jour les statistiques en fonction du type
    if stat_type == "tiqué_créer":
        tickets_created = int(stats[0][1]) + 1
        get_db("UPDATE state SET tiqué_créer = %s WHERE id_user = %s", 
               (tickets_created, user_id))
    
    elif stat_type == "post_comm":
        # Vérifier si l'utilisateur a créé le ticket
        ticket = get_db("SELECT * FROM tiqué WHERE ID_tiqué = %s", (ticket_id,))
        is_creator = ticket and ticket[0][1] == user_id
        
        if not is_creator:
            # Incrémenter le nombre de tickets auxquels l'utilisateur a participé
            tickets_participated = int(stats[0][2]) + 1
            get_db("UPDATE state SET tiqué_partisipé = %s WHERE id_user = %s", 
                   (tickets_participated, user_id))
        
        # Incrémenter le nombre de commentaires
        comments = int(stats[0][3]) + 1
        get_db("UPDATE state SET comm = %s WHERE id_user = %s", 
               (comments, user_id))
    
    return True

def associate_hardware_to_ticket(ticket_id, hardware_id):
    """
    Associe un matériel à un ticket
    
    Args:
        ticket_id (str): ID du ticket
        hardware_id (int): ID du matériel
    
    Returns:
        bool: True si l'association a été créée avec succès
    """
    # Vérifier si le ticket existe
    ticket = get_db(f"SELECT * FROM tiqué WHERE ID_tiqué = '{ticket_id}'")
    if not ticket:
        raise ValueError(f"Le ticket {ticket_id} n'existe pas")
    
    # Vérifier si le matériel existe
    hardware = get_db("SELECT * FROM materiel WHERE id = %s", (hardware_id,))
    if not hardware:
        raise ValueError(f"Le matériel avec ID {hardware_id} n'existe pas")
    
    # Vérifier si l'association existe déjà
    existing = get_db("SELECT * FROM ticket_materiel WHERE id_ticket = %s AND id_materiel = %s", 
                     (ticket_id, hardware_id))
    if existing:
        return True  # L'association existe déjà
    
    # Créer l'association
    get_db("""
        INSERT INTO ticket_materiel (id_ticket, id_materiel, date_association)
        VALUES (%s, %s, %s)
    """, (ticket_id, hardware_id, str(datetime.date.today())))
    
    return True

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
        WHERE id_ticket = %s AND id_materiel = %s
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
        WHERE tm.id_ticket = %s
    """, (ticket_id,))
    
    return hardware_ids

def get_available_hardware():
    """
    Récupère la liste de tout le matériel disponible pour être associé à un ticket
    
    Returns:
        list: Liste de tout le matériel disponible
    """
    hardware = get_db("""
        SELECT m.id, m.nom, c.nom AS categorie, sc.nom AS sous_categorie, ssc.nom AS sous_sous_categorie
        FROM materiel m
        LEFT JOIN categorie c ON m.categorie = c.id
        LEFT JOIN sous_categorie sc ON m.sous_categorie = sc.id
        LEFT JOIN sous_sous_categorie ssc ON m.sous_sous_categorie = ssc.id
    """)
    
    return hardware

class SousTicketService:
    @staticmethod
    def creer_sous_ticket(parent_ticket_id, titre, description, priorite, createur_id, assigne_a=None):
        """
        Crée un nouveau sous-ticket
        """
        sous_ticket_id = str(uuid.uuid4())
        
        try:
            get_db("""
                INSERT INTO sous_tickets 
                (id, parent_ticket_id, titre, description, priorite, createur_id, assigne_a)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (sous_ticket_id, parent_ticket_id, titre, description, priorite, createur_id, assigne_a))
            
            # Mettre à jour le compteur de sous-tickets
            get_db("""
                UPDATE tiqué 
                SET nombre_sous_tickets = nombre_sous_tickets + 1
                WHERE ID_tiqué = %s
            """, (parent_ticket_id,))
            
            # Enregistrer dans l'historique
            get_db("""
                INSERT INTO sous_tickets_historique 
                (sous_ticket_id, user_id, type_modification, nouvelle_valeur)
                VALUES (%s, %s, 'creation', %s)
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
            get_db("""
                INSERT INTO sous_tickets_dependances (sous_ticket_id, depend_de_id)
                VALUES (%s, %s)
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
                SELECT statut FROM sous_tickets WHERE id = %s
            """, (sous_ticket_id,))[0][0]
            
            # Mettre à jour le statut
            get_db("""
                UPDATE sous_tickets 
                SET statut = %s,
                    date_resolution = CASE 
                        WHEN %s IN ('resolu', 'ferme') THEN NOW()
                        ELSE NULL
                    END
                WHERE id = %s
            """, (nouveau_statut, nouveau_statut, sous_ticket_id))
            
            # Enregistrer dans l'historique
            get_db("""
                INSERT INTO sous_tickets_historique 
                (sous_ticket_id, user_id, type_modification, ancienne_valeur, nouvelle_valeur)
                VALUES (%s, %s, 'statut', %s, %s)
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
                SELECT assigne_a FROM sous_tickets WHERE id = %s
            """, (sous_ticket_id,))[0][0]
            
            # Mettre à jour l'assignation
            get_db("""
                UPDATE sous_tickets SET assigne_a = %s WHERE id = %s
            """, (assigne_a, sous_ticket_id))
            
            # Enregistrer dans l'historique
            get_db("""
                INSERT INTO sous_tickets_historique 
                (sous_ticket_id, user_id, type_modification, ancienne_valeur, nouvelle_valeur)
                VALUES (%s, %s, 'assignation', %s, %s)
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
            get_db("""
                INSERT INTO sous_tickets_commentaires 
                (sous_ticket_id, user_id, commentaire)
                VALUES (%s, %s, %s)
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
            sous_tickets = get_db("""
                SELECT st.*, u1.name as createur_name, u2.name as assigne_name
                FROM sous_tickets st
                LEFT JOIN USEUR u1 ON st.createur_id = u1.ID
                LEFT JOIN USEUR u2 ON st.assigne_a = u2.ID
                WHERE st.parent_ticket_id = %s
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