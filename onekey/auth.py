import secrets
import string
import re
import argon2
from datetime import datetime, timedelta
import jwt
from utils.db import get_db, log_activity

# Constantes pour la génération d'identifiants et de tokens
TOKEN_LENGTH = 64
ID_LENGTH = 24
JWT_SECRET = "glpibis_secret_key"  # À remplacer par une clé sécurisée en production

def generate_id():
    """
    Génère un identifiant unique pour les utilisateurs
    
    Returns:
        str: Identifiant unique
    """
    valid_chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(valid_chars) for _ in range(ID_LENGTH))

def generate_token():
    """
    Génère un token d'authentification unique
    
    Returns:
        str: Token d'authentification
    """
    valid_chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(valid_chars) for _ in range(TOKEN_LENGTH))

def validate_password(password):
    """
    Vérifie que le mot de passe respecte les critères de complexité
    
    Args:
        password (str): Mot de passe à vérifier
    
    Returns:
        bool: True si le mot de passe est valide
    """
    # Au moins 8 caractères
    if len(password) < 8:
        return False
    
    # Au moins une lettre majuscule
    if not re.search(r'[A-Z]', password):
        return False
    
    # Au moins une lettre minuscule
    if not re.search(r'[a-z]', password):
        return False
    
    # Au moins un chiffre
    if not re.search(r'[0-9]', password):
        return False
    
    # Au moins un caractère spécial
    if not re.search(r'[^A-Za-z0-9]', password):
        return False
    
    return True

def register_user(name, age, tel, email, password):
    """
    Enregistre un nouvel utilisateur dans le système
    
    Args:
        name (str): Nom de l'utilisateur
        age (int): Âge de l'utilisateur
        tel (str): Numéro de téléphone
        email (str): Adresse e-mail
        password (str): Mot de passe
    
    Returns:
        str: ID de l'utilisateur créé, ou None si échec
    
    Raises:
        ValueError: Si les données d'entrée sont invalides
    """
    # Vérifier que l'email n'est pas déjà utilisé
    existing_user = get_db("SELECT * FROM USEUR WHERE email = %s", (email,))
    if existing_user:
        raise ValueError("Cette adresse e-mail est déjà utilisée")
    
    # Vérifier que le mot de passe respecte les critères de complexité
    if not validate_password(password):
        raise ValueError("Le mot de passe ne respecte pas les critères de complexité")
    
    # Générer un identifiant unique
    user_id = generate_id()
    
    # Hasher le mot de passe
    ph = argon2.PasswordHasher()
    password_hash = ph.hash(password)
    
    # Préparer les données
    data = {
        'ID': user_id,
        'name': name,
        'age': int(age),
        'tel': tel,
        'password': password_hash,
        'email': email,
        'compte_date': datetime.now().strftime('%Y-%m-%d')
    }
    
    # Insérer l'utilisateur dans la base de données
    try:
        get_db("""
            INSERT INTO USEUR (ID, name, age, tel, password, email, compte_date)
            VALUES (%(ID)s, %(name)s, %(age)s, %(tel)s, %(password)s, %(email)s, %(compte_date)s)
        """, data)
        
        # Initialiser les statistiques de l'utilisateur
        get_db("INSERT INTO state (id_user, tiqué_créer, tiqué_partisipé, comm) VALUES (%s, 0, 0, 0)", 
               (user_id,))
        
        log_activity(user_id, 'register', 'auth', f"Création du compte utilisateur {email}")
        
        return user_id
    except Exception as e:
        print(f"Erreur lors de la création du compte: {e}")
        return None

def login_user(email, password):
    """
    Authentifie un utilisateur et crée une session
    
    Args:
        email (str): Adresse e-mail de l'utilisateur
        password (str): Mot de passe
    
    Returns:
        dict: Dictionnaire avec les infos de l'utilisateur et le status de l'authentification
    """
    # Récupérer l'utilisateur
    users = get_db("SELECT * FROM USEUR WHERE email = %s", (email,))
    if not users:
        return {'status': 'error', 'message': 'Email ou mot de passe incorrect'}
    
    user = users[0]
    user_id = user[0]
    username = user[1]
    
    # Vérifier le mot de passe
    ph = argon2.PasswordHasher()
    try:
        ph.verify(user[4], password)
    except argon2.exceptions.VerifyMismatchError:
        log_activity(user_id, 'login_failed', 'auth', f"Tentative de connexion échouée pour {email}")
        return {'status': 'error', 'message': 'Email ou mot de passe incorrect'}
    
    # Créer une session
    token = generate_token()
    
    # Déterminer la durée de la session à partir de la configuration
    from utils.db import load_config
    config = load_config()
    session_duration_hours = config.get('app_settings', {}).get('session_duration_hours', 24)
    expiry_date = datetime.now() + timedelta(hours=session_duration_hours)
    
    # Enregistrer la session dans la base de données
    get_db("""
        INSERT INTO sessions (user_id, token, expiry_date)
        VALUES (%s, %s, %s)
    """, (user_id, token, expiry_date))
    
    # Vérifier si l'utilisateur a des rôles spéciaux
    is_admin = bool(get_db("SELECT * FROM admin WHERE id_user = %s", (user_id,)))
    is_tech = bool(get_db("SELECT * FROM technicien WHERE id_user = %s", (user_id,)))
    role = 'admin' if is_admin else 'technician' if is_tech else 'user'
    
    log_activity(user_id, 'login', 'auth', f"Connexion réussie pour {email}")
    
    # Retourner un dictionnaire avec les informations de session
    return {
        'status': 'success',
        'user_id': user_id,
        'username': username,
        'email': email,
        'token': token,
        'role': role
    }

def validate_session(token):
    """
    Vérifie si une session est valide
    
    Args:
        token (str): Token de session
    
    Returns:
        str: ID de l'utilisateur si la session est valide, None sinon
    """
    if not token:
        return None
    
    # Rechercher la session dans la base de données
    sessions = get_db("""
        SELECT user_id FROM sessions 
        WHERE token = %s AND expiry_date > %s
    """, (token, datetime.now()))
    
    if not sessions:
        return None
    
    return sessions[0][0]

def logout_user(token):
    """
    Déconnecte un utilisateur en supprimant sa session
    
    Args:
        token (str): Token de session
    
    Returns:
        bool: True si la déconnexion est réussie
    """
    # Récupérer l'ID utilisateur avant de supprimer la session
    user_id = validate_session(token)
    
    if user_id:
        # Supprimer la session
        get_db("DELETE FROM sessions WHERE token = %s", (token,))
        log_activity(user_id, 'logout', 'auth', "Déconnexion")
        return True
    
    return False

def create_admin(user_id):
    """
    Donne les droits d'administrateur à un utilisateur
    
    Args:
        user_id (str): ID de l'utilisateur
    
    Returns:
        bool: True si l'opération est réussie
    """
    # Vérifier que l'utilisateur existe
    users = get_db("SELECT * FROM USEUR WHERE ID = %s", (user_id,))
    if not users:
        return False
    
    # Vérifier si l'utilisateur est déjà admin
    admin = get_db("SELECT * FROM admin WHERE id_user = %s", (user_id,))
    if admin:
        return True
    
    # Créer l'entrée admin
    get_db("INSERT INTO admin (id_user) VALUES (%s)", (user_id,))
    log_activity(user_id, 'promote', 'auth', "Promotion au rang d'administrateur")
    
    return True

def create_technician(user_id, speciality=None):
    """
    Donne les droits de technicien à un utilisateur
    
    Args:
        user_id (str): ID de l'utilisateur
        speciality (str, optional): Spécialité du technicien
    
    Returns:
        bool: True si l'opération est réussie
    """
    # Vérifier que l'utilisateur existe
    users = get_db("SELECT * FROM USEUR WHERE ID = %s", (user_id,))
    if not users:
        return False
    
    # Vérifier si l'utilisateur est déjà technicien
    tech = get_db("SELECT * FROM technicien WHERE id_user = %s", (user_id,))
    if tech:
        # Mettre à jour la spécialité si elle est fournie
        if speciality:
            get_db("UPDATE technicien SET specialite = %s WHERE id_user = %s", (speciality, user_id))
        return True
    
    # Créer l'entrée technicien
    get_db("INSERT INTO technicien (id_user, specialite) VALUES (%s, %s)", (user_id, speciality))
    log_activity(user_id, 'promote', 'auth', "Promotion au rang de technicien")
    
    return True

def generate_jwt_token(user_id):
    """
    Génère un token JWT pour l'authentification API
    
    Args:
        user_id (str): ID de l'utilisateur
    
    Returns:
        str: Token JWT
    """
    # Récupérer les informations de l'utilisateur
    users = get_db("SELECT * FROM USEUR WHERE ID = %s", (user_id,))
    if not users:
        return None
    
    user = users[0]
    
    # Récupérer le rôle
    is_admin = bool(get_db("SELECT * FROM admin WHERE id_user = %s", (user_id,)))
    is_tech = bool(get_db("SELECT * FROM technicien WHERE id_user = %s", (user_id,)))
    role = 'admin' if is_admin else 'technician' if is_tech else 'user'
    
    # Créer le payload
    payload = {
        'sub': user_id,
        'name': user[1],
        'email': user[5],
        'role': role,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(days=1)
    }
    
    # Générer le token
    token = jwt.encode(payload, JWT_SECRET, algorithm='HS256')
    
    return token

def validate_jwt_token(token):
    """
    Vérifie la validité d'un token JWT
    
    Args:
        token (str): Token JWT
    
    Returns:
        dict: Payload du token si valide, None sinon
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        print("Token expiré")
        return None
    except jwt.InvalidTokenError:
        print("Token invalide")
        return None