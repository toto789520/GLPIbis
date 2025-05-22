import datetime
import secrets
import csv
import json
from io import StringIO
from utils.db_manager import get_db, log_activity

def add_item(nom, categorie_id, sous_categorie_id, sous_sous_categorie_id, date_creation=None, qr_code=None):
    """
    Ajoute un nouvel élément à l'inventaire
    
    Args:
        nom (str): Nom de l'élément
        categorie_id (int): ID de la catégorie
        sous_categorie_id (int): ID de la sous-catégorie
        sous_sous_categorie_id (int): ID de la sous-sous-catégorie
        date_creation (str, optional): Date de création au format YYYY-MM-DD
        qr_code (str, optional): Code QR personnalisé
    
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
    
    # Utiliser la date fournie ou la date actuelle
    if not date_creation:
        date_creation = datetime.date.today().isoformat()
    
    # Générer un ID unique pour le QR code si non fourni
    if not qr_code:
        qr_code = secrets.token_hex(4).upper()
    
    # Insérer le matériel dans la base de données
    data = {
        'nom': nom,
        'categorie': categorie_id,
        'sous_categorie': sous_categorie_id,
        'sous_sous_categorie': sous_sous_categorie_id,
        'date_creation': date_creation,
        'qr_code': qr_code
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

def link_item_to_ticket(item_id, ticket):
    """
    Lie un élément à un ticket
    
    Args:
        item_id (int): ID de l'élément
        ticket (int): ID du ticket
    
    Returns:
        bool: True si l'association a été créée avec succès
    """
    get_db("INSERT INTO ticket_materiel (id_materiel, id_ticket) VALUES (%s, %s)", (item_id, ticket))
    return True

# Fonctions d'import/export
def export_inventory_csv():
    """
    Exporte l'inventaire au format CSV
    """
    output = StringIO()
    writer = csv.writer(output)
    
    # En-têtes
    writer.writerow(['ID', 'Nom', 'Catégorie', 'Sous-catégorie', 'Sous-sous-catégorie', 
                    'Date création', 'Code QR', 'Bâtiment', 'Étage', 'Salle', 'Description'])
    
    # Récupérer les données
    items = get_db("""
        SELECT m.*, c.nom as cat_nom, sc.nom as scat_nom, ssc.nom as sscat_nom,
               l.batiment, l.etage, l.salle, l.description
        FROM materiel m
        JOIN categorie c ON m.categorie = c.id
        JOIN sous_categorie sc ON m.sous_categorie = sc.id
        JOIN sous_sous_categorie ssc ON m.sous_sous_categorie = ssc.id
        LEFT JOIN localisation l ON m.id_localisation = l.id
    """)
    
    # Écrire les données
    for item in items:
        writer.writerow([
            item[0],  # ID
            item[1],  # Nom
            item['cat_nom'],
            item['scat_nom'],
            item['sscat_nom'],
            item[5],  # Date création
            item[6],  # QR Code
            item['batiment'] or '',
            item['etage'] or '',
            item['salle'] or '',
            item['description'] or ''
        ])
    
    return output.getvalue()

def export_inventory_json():
    """
    Exporte l'inventaire au format JSON
    """
    # Récupérer les données avec la même requête que pour le CSV
    items = get_db("""
        SELECT m.*, c.nom as cat_nom, sc.nom as scat_nom, ssc.nom as sscat_nom,
               l.batiment, l.etage, l.salle, l.description
        FROM materiel m
        JOIN categorie c ON m.categorie = c.id
        JOIN sous_categorie sc ON m.sous_categorie = sc.id
        JOIN sous_sous_categorie ssc ON m.sous_sous_categorie = ssc.id
        LEFT JOIN localisation l ON m.id_localisation = l.id
    """)
    
    # Convertir en format JSON
    inventory_data = []
    for item in items:
        inventory_data.append({
            'id': item[0],
            'nom': item[1],
            'categorie': item['cat_nom'],
            'sous_categorie': item['scat_nom'],
            'sous_sous_categorie': item['sscat_nom'],
            'date_creation': item[5].isoformat(),
            'qr_code': item[6],
            'localisation': {
                'batiment': item['batiment'],
                'etage': item['etage'],
                'salle': item['salle'],
                'description': item['description']
            } if item['batiment'] else None
        })
    
    return json.dumps(inventory_data, ensure_ascii=False, indent=2)

def import_inventory_csv(file_content):
    """
    Importe l'inventaire depuis un fichier CSV
    """
    reader = csv.DictReader(StringIO(file_content))
    imported_count = 0
    errors = []
    
    for row in reader:
        try:
            # Récupérer ou créer les catégories
            cat_id = get_or_create_category(row['Catégorie'])
            scat_id = get_or_create_subcategory(row['Sous-catégorie'], cat_id)
            sscat_id = get_or_create_subsubcategory(row['Sous-sous-catégorie'], scat_id)
            
            # Créer ou mettre à jour la localisation si présente
            location_id = None
            if row['Bâtiment']:
                location_id = add_location(
                    row['Bâtiment'],
                    row['Étage'],
                    row['Salle'],
                    row['Description']
                )
            
            # Ajouter ou mettre à jour le matériel
            if row.get('ID'):
                # Mise à jour
                update_item(
                    int(row['ID']),
                    row['Nom'],
                    cat_id,
                    scat_id,
                    sscat_id,
                    row['Date création'],
                    row['Code QR'],
                    location_id
                )
            else:
                # Création
                add_item(
                    row['Nom'],
                    cat_id,
                    scat_id,
                    sscat_id,
                    row['Date création'],
                    row['Code QR']
                )
            
            imported_count += 1
            
        except Exception as e:
            errors.append(f"Erreur ligne {reader.line_num}: {str(e)}")
    
    return imported_count, errors

def get_or_create_category(name):
    """Récupère ou crée une catégorie"""
    cats = get_db("SELECT id FROM categorie WHERE nom = %s", (name,))
    if cats:
        return cats[0][0]
    
    get_db("INSERT INTO categorie (nom) VALUES (%s)", (name,))
    return get_db("SELECT LAST_INSERT_ID()")[0][0]

def get_or_create_subcategory(name, category_id):
    """Récupère ou crée une sous-catégorie"""
    scats = get_db("SELECT id FROM sous_categorie WHERE nom = %s AND id_categorie = %s", 
                   (name, category_id))
    if scats:
        return scats[0][0]
    
    get_db("INSERT INTO sous_categorie (nom, id_categorie) VALUES (%s, %s)", 
           (name, category_id))
    return get_db("SELECT LAST_INSERT_ID()")[0][0]

def get_or_create_subsubcategory(name, subcategory_id):
    """Récupère ou crée une sous-sous-catégorie"""
    sscats = get_db("SELECT id FROM sous_sous_categorie WHERE nom = %s AND id_sous_categorie = %s", 
                    (name, subcategory_id))
    if sscats:
        return sscats[0][0]
    
    get_db("INSERT INTO sous_sous_categorie (nom, id_sous_categorie) VALUES (%s, %s)", 
           (name, subcategory_id))
    return get_db("SELECT LAST_INSERT_ID()")[0][0]

# Fonctions pour la gestion des localisations
def add_location(batiment, etage=None, salle=None, description=None):
    """Ajoute une nouvelle localisation"""
    sql = """
        INSERT INTO localisation (batiment, etage, salle, description)
        VALUES (%s, %s, %s, %s)
    """
    get_db(sql, (batiment, etage, salle, description))
    return get_db("SELECT LAST_INSERT_ID()")[0][0]

def get_locations():
    """Récupère toutes les localisations"""
    return get_db("SELECT * FROM localisation ORDER BY batiment, etage, salle")

def get_location(location_id):
    """Récupère une localisation par son ID"""
    locations = get_db("SELECT * FROM localisation WHERE id = %s", (location_id,))
    return locations[0] if locations else None

def update_item_location(item_id, location_id):
    """Met à jour la localisation d'un matériel"""
    sql = "UPDATE materiel SET id_localisation = %s WHERE id = %s"
    get_db(sql, (location_id, item_id))

def get_item_location(item_id):
    """Récupère la localisation d'un matériel"""
    sql = """
        SELECT l.* FROM localisation l
        JOIN materiel m ON m.id_localisation = l.id
        WHERE m.id = %s
    """
    locations = get_db(sql, (item_id,))
    return locations[0] if locations else None

# Fonctions pour la gestion des prêts
def create_loan(item_id, user_id, return_date, notes=None):
    """Crée un nouveau prêt"""
    # Vérifier si l'item est déjà emprunté
    existing_loan = get_db("""
        SELECT id FROM pret 
        WHERE id_materiel = %s AND statut = 'en_cours'
    """, (item_id,))
    
    if existing_loan:
        raise ValueError("Ce matériel est déjà emprunté")
    
    sql = """
        INSERT INTO pret (id_materiel, id_emprunteur, date_retour_prevue, notes)
        VALUES (%s, %s, %s, %s)
    """
    get_db(sql, (item_id, user_id, return_date, notes))
    return get_db("SELECT LAST_INSERT_ID()")[0][0]

def return_item(loan_id):
    """Enregistre le retour d'un matériel"""
    sql = """
        UPDATE pret 
        SET date_retour = NOW(), statut = 'retourne'
        WHERE id = %s
    """
    get_db(sql, (loan_id,))

def extend_loan(loan_id, new_return_date, reason=None):
    """Prolonge un prêt"""
    sql = """
        UPDATE pret 
        SET date_retour_prevue = %s,
            notes = CONCAT(IFNULL(notes, ''), '\nProlongation jusqu''au ', %s, ': ', %s)
        WHERE id = %s
    """
    get_db(sql, (new_return_date, new_return_date, reason or 'Aucune raison spécifiée', loan_id))

def get_active_loans():
    """Récupère tous les prêts en cours"""
    sql = """
        SELECT p.*, m.nom as materiel_nom, u.name as emprunteur_nom
        FROM pret p
        JOIN materiel m ON p.id_materiel = m.id
        JOIN USEUR u ON p.id_emprunteur = u.ID
        WHERE p.statut IN ('en_cours', 'en_retard')
    """
    return get_db(sql)

def get_item_loan_history(item_id):
    """Récupère l'historique des prêts d'un matériel"""
    sql = """
        SELECT p.*, u.name as emprunteur_nom
        FROM pret p
        JOIN USEUR u ON p.id_emprunteur = u.ID
        WHERE p.id_materiel = %s
        ORDER BY p.date_pret DESC
    """
    return get_db(sql, (item_id,))

def add_intervention(item_id, user_id, type_intervention, description):
    """Ajoute une intervention sur un matériel"""
    sql = """
        INSERT INTO intervention (id_materiel, id_technicien, type, description, date_debut)
        VALUES (%s, %s, %s, %s, NOW())
    """
    get_db(sql, (item_id, user_id, type_intervention, description))
    return get_db("SELECT LAST_INSERT_ID()")[0][0]

def get_item_interventions(item_id):
    """Récupère l'historique des interventions d'un matériel"""
    sql = """
        SELECT i.*, u.name as technicien_nom
        FROM intervention i
        JOIN USEUR u ON i.id_technicien = u.ID
        WHERE i.id_materiel = %s
        ORDER BY i.date_debut DESC
    """
    return get_db(sql, (item_id,))

def close_intervention(intervention_id):
    """Termine une intervention"""
    sql = """
        UPDATE intervention
        SET date_fin = NOW(), statut = 'termine'
        WHERE id = %s
    """
    get_db(sql, (intervention_id,))