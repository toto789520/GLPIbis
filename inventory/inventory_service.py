import datetime
import secrets
from utils.db import get_db, log_activity

def add_item(nom, categorie_id, sous_categorie_id, sous_sous_categorie_id):
    """
    Ajoute un nouvel élément à l'inventaire
    
    Args:
        nom (str): Nom de l'élément
        categorie_id (int): ID de la catégorie
        sous_categorie_id (int): ID de la sous-catégorie
        sous_sous_categorie_id (int): ID de la sous-sous-catégorie
    
    Returns:
        int: ID de l'élément ajouté
    """
    # Vérifier que les catégories existent
    categorie = get_db("SELECT * FROM categorie WHERE id = %s", (categorie_id,))
    if not categorie:
        raise ValueError(f"La catégorie avec l'ID {categorie_id} n'existe pas")
    
    sous_categorie = get_db("SELECT * FROM sous_categorie WHERE id = %s", (sous_categorie_id,))
    if not sous_categorie:
        raise ValueError(f"La sous-catégorie avec l'ID {sous_categorie_id} n'existe pas")
    
    sous_sous_categorie = get_db("SELECT * FROM sous_sous_categorie WHERE id = %s", (sous_sous_categorie_id,))
    if not sous_sous_categorie:
        raise ValueError(f"La sous-sous-catégorie avec l'ID {sous_sous_categorie_id} n'existe pas")
    
    # Générer un ID unique pour le QR code
    qr_id = secrets.token_hex(4).upper()
    
    # Insérer le matériel dans la base de données
    data = {
        'nom': nom,
        'categorie': categorie_id,
        'sous_categorie': sous_categorie_id,
        'sous_sous_categorie': sous_sous_categorie_id,
        'date_creation': datetime.date.today().isoformat(),
        'qr_code': qr_id
    }
    
    get_db("""
        INSERT INTO materiel (nom, categorie, sous_categorie, sous_sous_categorie, date_creation, qr_code) 
        VALUES (%(nom)s, %(categorie)s, %(sous_categorie)s, %(sous_sous_categorie)s, %(date_creation)s, %(qr_code)s)
    """, data)
    
    # Récupérer l'ID du matériel créé
    item_id = get_db("SELECT LAST_INSERT_ID()")[0][0]
    
    return item_id

def delete_item(item_id):
    """
    Supprime un élément de l'inventaire
    
    Args:
        item_id (int): ID de l'élément à supprimer
    
    Returns:
        bool: True si l'élément a été supprimé avec succès
    """
    # Vérifier que l'élément existe
    item = get_db("SELECT * FROM materiel WHERE id = %s", (item_id,))
    if not item:
        raise ValueError(f"Le matériel avec l'ID {item_id} n'existe pas")
    
    # Vérifier si l'élément est associé à des tickets
    ticket_associations = get_db("SELECT * FROM ticket_materiel WHERE id_materiel = %s", (item_id,))
    
    # Si des associations existent, les supprimer d'abord
    if ticket_associations:
        get_db("DELETE FROM ticket_materiel WHERE id_materiel = %s", (item_id,))
    
    # Supprimer l'élément
    get_db("DELETE FROM materiel WHERE id = %s", (item_id,))
    
    return True

def get_item_by_id(item_id):
    """
    Récupère un élément par son ID
    
    Args:
        item_id (int): ID de l'élément à récupérer
    
    Returns:
        tuple: Informations sur l'élément ou None s'il n'existe pas
    """
    items = get_db("SELECT * FROM materiel WHERE id = %s", (item_id,))
    if not items:
        return None
    
    return items[0]

def list_items(category_id=None, sous_category_id=None):
    """
    Liste tous les éléments de l'inventaire, avec filtrage optionnel
    
    Args:
        category_id (int, optional): ID de la catégorie pour filtrer
        sous_category_id (int, optional): ID de la sous-catégorie pour filtrer
    
    Returns:
        list: Liste des éléments correspondant aux filtres
    """
    if category_id and sous_category_id:
        items = get_db("""
            SELECT m.*, c.nom AS categorie_nom, sc.nom AS sous_categorie_nom, ssc.nom AS sous_sous_categorie_nom 
            FROM materiel m
            JOIN categorie c ON m.categorie = c.id
            JOIN sous_categorie sc ON m.sous_categorie = sc.id
            JOIN sous_sous_categorie ssc ON m.sous_sous_categorie = ssc.id
            WHERE m.categorie = %s AND m.sous_categorie = %s
        """, (category_id, sous_category_id))
    elif category_id:
        items = get_db("""
            SELECT m.*, c.nom AS categorie_nom, sc.nom AS sous_categorie_nom, ssc.nom AS sous_sous_categorie_nom 
            FROM materiel m
            JOIN categorie c ON m.categorie = c.id
            JOIN sous_categorie sc ON m.sous_categorie = sc.id
            JOIN sous_sous_categorie ssc ON m.sous_sous_categorie = ssc.id
            WHERE m.categorie = %s
        """, (category_id,))
    else:
        items = get_db("""
            SELECT m.*, c.nom AS categorie_nom, sc.nom AS sous_categorie_nom, ssc.nom AS sous_sous_categorie_nom 
            FROM materiel m
            JOIN categorie c ON m.categorie = c.id
            JOIN sous_categorie sc ON m.sous_categorie = sc.id
            JOIN sous_sous_categorie ssc ON m.sous_sous_categorie = ssc.id
        """)
    
    return items

def get_categories():
    """
    Récupère toutes les catégories de matériel
    
    Returns:
        list: Liste des catégories
    """
    return get_db("SELECT * FROM categorie")

def get_sous_categories(categorie_id):
    """
    Récupère toutes les sous-catégories d'une catégorie
    
    Args:
        categorie_id (int): ID de la catégorie
    
    Returns:
        list: Liste des sous-catégories
    """
    return get_db("SELECT * FROM sous_categorie WHERE id_categorie = %s", (categorie_id,))

def get_sous_sous_categories(sous_categorie_id):
    """
    Récupère toutes les sous-sous-catégories d'une sous-catégorie
    
    Args:
        sous_categorie_id (int): ID de la sous-catégorie
    
    Returns:
        list: Liste des sous-sous-catégories
    """
    return get_db("SELECT * FROM sous_sous_categorie WHERE id_sous_categorie = %s", (sous_categorie_id,))

def link_item_to_ticket(item_id, ticket_id):
    """
    Associe un élément à un ticket
    
    Args:
        item_id (int): ID de l'élément
        ticket_id (str): ID du ticket
    
    Returns:
        bool: True si l'association a été créée avec succès
    """
    # Vérifier que l'élément existe
    item = get_db("SELECT * FROM materiel WHERE id = %s", (item_id,))
    if not item:
        raise ValueError(f"Le matériel avec l'ID {item_id} n'existe pas")
    
    # Vérifier que le ticket existe
    ticket = get_db("SELECT * FROM tiqué WHERE ID_tiqué = %s", (ticket_id,))
    if not ticket:
        raise ValueError(f"Le ticket avec l'ID {ticket_id} n'existe pas")
    
    # Vérifier si l'association existe déjà
    existing = get_db("SELECT * FROM ticket_materiel WHERE id_ticket = %s AND id_materiel = %s", 
                     (ticket_id, item_id))
    if existing:
        return True  # L'association existe déjà, rien à faire
    
    # Créer l'association
    get_db("INSERT INTO ticket_materiel (id_ticket, id_materiel, date_association) VALUES (%s, %s, %s)", 
           (ticket_id, item_id, datetime.date.today().isoformat()))
    
    return True

def unlink_item_from_ticket(item_id, ticket_id):
    """
    Dissocie un élément d'un ticket
    
    Args:
        item_id (int): ID de l'élément
        ticket_id (str): ID du ticket
    
    Returns:
        bool: True si l'association a été supprimée avec succès
    """
    get_db("DELETE FROM ticket_materiel WHERE id_ticket = %s AND id_materiel = %s", 
           (ticket_id, item_id))
    
    return True

def get_items_by_ticket(ticket_id):
    """
    Récupère tous les éléments associés à un ticket
    
    Args:
        ticket_id (str): ID du ticket
    
    Returns:
        list: Liste des éléments associés au ticket
    """
    items = get_db("""
        SELECT m.*, c.nom AS categorie_nom, sc.nom AS sous_categorie_nom, ssc.nom AS sous_sous_categorie_nom 
        FROM materiel m
        JOIN ticket_materiel tm ON m.id = tm.id_materiel
        JOIN categorie c ON m.categorie = c.id
        JOIN sous_categorie sc ON m.sous_categorie = sc.id
        JOIN sous_sous_categorie ssc ON m.sous_sous_categorie = ssc.id
        WHERE tm.id_ticket = %s
    """, (ticket_id,))
    
    return items