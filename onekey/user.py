from utils.db_manager import get_db

def get_user_info(user_id):
    """
    Récupère les informations complètes d'un utilisateur
    
    Args:
        user_id (str): ID de l'utilisateur
    
    Returns:
        dict: Informations complètes de l'utilisateur ou None si non trouvé
    """
    if not user_id:
        return None
    
    # Récupération des informations de base
    users = get_db("SELECT * FROM USEUR WHERE ID = ?", (user_id,))
    if not users:
        return None
    
    user = users[0]
    
    # Récupération des statistiques
    stats = get_db("SELECT * FROM state WHERE id_user = ?", (user_id,))
    
    # Construction de l'objet utilisateur avec gestion flexible de la structure
    user_info = {
        'id': user[0],           # ID
        'name': user[1] if len(user) > 1 else '',         # name
        'age': user[2] if len(user) > 2 else None,        # age
        'tel': user[3] if len(user) > 3 else '',          # tel
        'email': user[5] if len(user) > 5 else (user[2] if len(user) > 2 else ''),  # email
        'creation_date': user[6] if len(user) > 6 else '',  # creation_date
        'role': user[7] if len(user) > 7 else get_user_role(user_id),  # role ou récupération
        'stats': {
            'tickets_created': stats[0][2] if stats and len(stats[0]) > 2 else 0,      # tickets_created
            'tickets_participated': stats[0][3] if stats and len(stats[0]) > 3 else 0, # tickets_participated
            'comments': stats[0][4] if stats and len(stats[0]) > 4 else 0              # comments
        }
    }
    
    return user_info

def get_user_role(user_id):
    """
    Récupère le rôle d'un utilisateur
    
    Args:
        user_id (str): ID de l'utilisateur
    
    Returns:
        str: Rôle de l'utilisateur ('admin', 'technician', 'user')
    """
    # Vérifier si l'utilisateur est un admin
    admin = get_db("SELECT * FROM admin WHERE id_user = ?", (user_id,))
    if admin:
        return 'admin'
    
    # Vérifier si l'utilisateur est un technicien
    tech = get_db("SELECT * FROM technicien WHERE id_user = ?", (user_id,))
    if tech:
        return 'technician'
    
    # Par défaut, c'est un utilisateur standard
    return 'user'

def update_user_info(user_id, data):
    """
    Met à jour les informations d'un utilisateur
    
    Args:
        user_id (str): ID de l'utilisateur
        data (dict): Données à mettre à jour (clés: 'name', 'age', 'tel', 'email')
    
    Returns:
        bool: True si la mise à jour est réussie
    """
    fields_to_update = []
    params = []
    
    # Construire la requête SQL en fonction des champs à mettre à jour
    for field in ['name', 'age', 'tel', 'email']:
        if field in data and data[field]:
            fields_to_update.append(f"{field} = ?")
            params.append(data[field])
    
    if not fields_to_update:
        return False
    
    # Ajouter l'ID utilisateur aux paramètres
    params.append(user_id)
    
    # Exécuter la requête
    get_db(f"""
        UPDATE USEUR 
        SET {', '.join(fields_to_update)}
        WHERE ID = ?
    """, params)
    
    return True

def change_password(user_id, current_password, new_password):
    """
    Change le mot de passe d'un utilisateur
    
    Args:
        user_id (str): ID de l'utilisateur
        current_password (str): Mot de passe actuel
        new_password (str): Nouveau mot de passe
    
    Returns:
        bool: True si le changement est réussi
    
    Raises:
        ValueError: Si le mot de passe actuel est incorrect ou si le nouveau mot de passe est invalide
    """
    # Importer ici pour éviter les imports circulaires
    from .auth import validate_password
    import argon2
    
    # Vérifier le mot de passe actuel
    users = get_db("SELECT ID, password FROM USEUR WHERE ID = ?", (user_id,))
    if not users:
        raise ValueError("Utilisateur non trouvé")
    
    user = users[0]
    current_hash = user[1]  # password est en position 1 dans cette requête
    
    # Vérifier le mot de passe actuel
    ph = argon2.PasswordHasher()
    try:
        ph.verify(current_hash, current_password)
    except argon2.exceptions.VerifyMismatchError:
        raise ValueError("Mot de passe actuel incorrect")
    
    # Vérifier si le nouveau mot de passe est valide
    if not validate_password(new_password):
        raise ValueError("Le nouveau mot de passe ne respecte pas les critères de complexité")
    
    # Hasher le nouveau mot de passe
    new_hash = ph.hash(new_password)
    
    # Mettre à jour le mot de passe
    get_db("UPDATE USEUR SET password = ? WHERE ID = ?", (new_hash, user_id))
    
    return True

def list_users(role=None):
    """
    Liste tous les utilisateurs, filtrés par rôle si spécifié
    
    Args:
        role (str, optional): Rôle pour filtrer ('admin', 'technician', 'user')
    
    Returns:
        list: Liste des utilisateurs
    """
    if role == 'admin':
        # Récupération des administrateurs
        admin_ids = get_db("SELECT id_user FROM admin")
        if not admin_ids:
            return []
        
        placeholder = ', '.join(['?'] * len(admin_ids))
        admin_ids = [admin_id[0] for admin_id in admin_ids]
        
        users = get_db(f"SELECT ID, name, age, tel, email, creation_date, role FROM USEUR WHERE ID IN ({placeholder})", admin_ids)
    
    elif role == 'technician':
        # Récupération des techniciens
        tech_ids = get_db("SELECT id_user FROM technicien")
        if not tech_ids:
            return []
        
        placeholder = ', '.join(['?'] * len(tech_ids))
        tech_ids = [tech_id[0] for tech_id in tech_ids]
        
        users = get_db(f"SELECT ID, name, age, tel, email, creation_date, role FROM USEUR WHERE ID IN ({placeholder})", tech_ids)
    
    else:
        # Récupération de tous les utilisateurs (sans password)
        users = get_db("SELECT ID, name, age, tel, email, creation_date, role FROM USEUR")
    
    # Formatage des résultats
    formatted_users = []
    for user in users:
        user_info = {
            'id': user[0],
            'name': user[1],
            'age': user[2],
            'tel': user[3],
            'email': user[4],
            'creation_date': user[5],
            'role': user[6] if len(user) > 6 and user[6] else get_user_role(user[0])
        }
        formatted_users.append(user_info)
    
    return formatted_users