import secrets
import string
import re
import argon2
from datetime import datetime, timedelta
import jwt
from utils.db_manager import get_db

def log_activity(user_id, action_type, module, description):
    try:
        query = """
        INSERT INTO activity_logs (user_id, action_type, module, description, timestamp)
        VALUES (?, ?, ?, ?, ?)
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        get_db(query, (user_id, action_type, module, description, timestamp))
        return True
    except Exception as e:
        print(f"Erreur lors de l'enregistrement de l'activité: {e}")
        return False

# Constantes pour la génération d'identifiants et de tokens
TOKEN_LENGTH = 64
ID_LENGTH = 24
JWT_SECRET = "glpibis_secret_key"  # À remplacer par une clé sécurisée en production

def generate_id(length=36):
    """
    Génère un identifiant unique aléatoire
    
    Args:
        length (int): Longueur de l'identifiant (par défaut 36 caractères)
    
    Returns:
        str: Identifiant généré
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

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
    if not any(c.isupper() for c in password):
        return False
    
    # Au moins une lettre minuscule
    if not any(c.islower() for c in password):
        return False
    
    # Au moins un chiffre
    if not any(c.isdigit() for c in password):
        return False
    
    # Au moins un caractère spécial
    if not re.search(r'[^A-Za-z0-9]', password):
        return False
    
    return True

def register_user(name, age, tel, email, password, role='user'):
    """
    Enregistre un nouvel utilisateur dans le système
    
    Args:
        name (str): Nom de l'utilisateur
        age (int): Âge de l'utilisateur
        tel (str): Numéro de téléphone
        email (str): Adresse e-mail
        password (str): Mot de passe
        role (str, optional): Rôle de l'utilisateur ('user', 'admin', 'technician'). Par défaut 'user'.
    
    Returns:
        str: ID de l'utilisateur créé, ou None si échec
    
    Raises:
        ValueError: Si les données d'entrée sont invalides
    """
    # Vérifier que l'email n'est pas déjà utilisé
    existing_user = get_db("SELECT * FROM USEUR WHERE email = ?", (email,), fetch=True)
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
    
    # Préparer les données avec la date d'inscription
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Insérer l'utilisateur de manière transactionnelle pour éviter les problèmes
    conn = None
    try:
        # Obtenir une connexion directe pour la transaction
        conn = get_db('connect')
        
        # Début de la transaction
        if hasattr(conn, 'isolation_level'):  # SQLite
            old_isolation = conn.isolation_level
            conn.isolation_level = None
            cursor = conn.cursor()
            cursor.execute('BEGIN TRANSACTION')
        
        # Insérer l'utilisateur
        cursor.execute("""
            INSERT INTO USEUR (ID, name, hashed_password, email, dete_de_creation, role, age, tel)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, name, password_hash, email, current_date, role, age or 0, tel or ''))
        
        # Initialiser les statistiques
        cursor.execute("""
            INSERT INTO state (id_user, tiqué_créer, tiqué_partisipé, comm)
            VALUES (?, 0, 0, 0)
        """, (user_id,))
        
        # Gérer les rôles spéciaux
        if role == 'admin':
            # Vérifier si la table admin existe
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='admin'")
            if cursor.fetchone():
                cursor.execute("INSERT INTO admin (id_user) VALUES (?)", (user_id,))
        
        elif role == 'technician':
            # Vérifier si la table technicien existe
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='technicien'")
            if cursor.fetchone():
                cursor.execute("INSERT INTO technicien (id_user, specialite) VALUES (?, ?)", (user_id, 'Général'))
        
        # Valider la transaction
        conn.commit()
        
        if hasattr(conn, 'isolation_level') and old_isolation is not None:  # SQLite
            conn.isolation_level = old_isolation
        
        # Vérifier si l'utilisateur a bien été créé
        cursor.execute("SELECT * FROM USEUR WHERE ID = ?", (user_id,))
        user_check = cursor.fetchone()
        
        if not user_check:
            print(f"ERREUR: L'utilisateur {email} n'a pas été créé malgré la transaction réussie")
            return None
        
        print(f"INFO: Utilisateur {email} créé avec succès - ID: {user_id}")
        
        # Journaliser l'activité
        try:
            log_activity(user_id, 'register', 'auth', f"Création du compte utilisateur {email} avec le rôle {role}")
        except Exception as e:
            print(f"INFO: Impossible de journaliser l'activité: {e}")
        
        return user_id
        
    except Exception as e:
        print(f"Erreur lors de la création du compte: {str(e)}")
        if conn and hasattr(conn, 'rollback'):
            try:
                conn.rollback()
            except:
                pass
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
    # Récupérer l'utilisateur - s'assurer que fetch=True pour obtenir les résultats
    users = get_db("SELECT ID, name, email, hashed_password FROM USEUR WHERE email = ?", (email,), fetch=True)
    
    # Debug pour voir ce qui est récupéré
    print(f"DEBUG - Utilisateur trouvé pour {email}: {users}")
    
    if not users:
        return {'status': 'error', 'message': 'Email ou mot de passe incorrect'}
    
    user = users[0]
    user_id = user[0]
    username = user[1]
    hashed_pw = user[3]
    
    # Vérifier le mot de passe
    ph = argon2.PasswordHasher()
    try:
        ph.verify(hashed_pw, password)
    except argon2.exceptions.VerifyMismatchError:
        log_activity(user_id, 'login_failed', 'auth', f"Tentative de connexion échouée pour {email}")
        return {'status': 'error', 'message': 'Email ou mot de passe incorrect'}
    
    # Mettre à jour la date de dernière connexion avec syntaxe SQLite
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    get_db("UPDATE USEUR SET derniere_connexion = ? WHERE ID = ?", (current_date, user_id))
    
    # Créer une session
    token = generate_token()
    print(f"DEBUG - login_user: Génération d'un nouveau token: {token[:5]}...")
    
    # Déterminer la durée de la session à partir de la configuration
    from utils.db_manager import load_config
    config = load_config()
    session_duration_hours = config.get('app_settings', {}).get('session_duration_hours', 24)
    expiry_date = (datetime.now() + timedelta(hours=session_duration_hours)).strftime("%Y-%m-%d %H:%M:%S")
    
    # Vérifier si la table sessions existe, sinon la créer
    try:
        get_db("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                token TEXT NOT NULL UNIQUE,
                expiry_date TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Utiliser une connexion directe pour transaction
        conn = get_db('connect')
        cursor = conn.cursor()
        
        try:
            # Supprimer les anciennes sessions de cet utilisateur pour éviter les problèmes
            cursor.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
            # Enregistrer la nouvelle session
            cursor.execute("""
                INSERT INTO sessions (user_id, token, expiry_date)
                VALUES (?, ?, ?)
            """, (user_id, token, expiry_date))
            conn.commit()
            
            # Vérifier que la session a bien été créée
            cursor.execute("SELECT user_id FROM sessions WHERE token = ?", (token,))
            session_check = cursor.fetchone()
            if not session_check:
                print(f"ERREUR - login_user: La session n'a pas été correctement créée pour {email}")
            else:
                print(f"DEBUG - login_user: Session créée avec succès pour {email}, token: {token[:5]}...")
                
        except Exception as e:
            conn.rollback()
            print(f"ERREUR - login_user: Erreur lors de la création de la session: {str(e)}")
            raise e
    
    except Exception as e:
        print(f"ERREUR - login_user: Erreur lors de la gestion de session: {str(e)}")
        return {'status': 'error', 'message': f'Erreur interne: {str(e)}'}
    
    # Vérifier si l'utilisateur a des rôles spéciaux
    is_admin = False
    is_tech = False
    role = 'user'
    
    try:
        # Vérifier si la table admin existe avec sqlite_master
        admin_check = get_db("SELECT name FROM sqlite_master WHERE type='table' AND name='admin'", fetch=True)
        if admin_check:
            admin_result = get_db("SELECT * FROM admin WHERE id_user = ?", (user_id,), fetch=True)
            is_admin = bool(admin_result)
        
        # Vérifier si la table technicien existe avec sqlite_master
        tech_check = get_db("SELECT name FROM sqlite_master WHERE type='table' AND name='technicien'", fetch=True)
        if tech_check:
            tech_result = get_db("SELECT * FROM technicien WHERE id_user = ?", (user_id,), fetch=True)
            is_tech = bool(tech_result)
        
        role = 'admin' if is_admin else 'technician' if is_tech else 'user'
    except Exception as e:
        print(f"ATTENTION - login_user: Erreur lors de la vérification des rôles: {e}")
        # Continuer avec le rôle par défaut 'user'
    
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
        print("DEBUG - validate_session: Pas de token fourni")
        return None
    
    # Vérifier si la table sessions existe
    table_check = get_db("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'", fetch=True)
    if not table_check:
        print("DEBUG - validate_session: La table sessions n'existe pas")
        return None
    
    # Format actuel de la date pour SQLite
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Rechercher la session dans la base de données avec syntaxe SQLite
    sessions = get_db("""
        SELECT user_id FROM sessions 
        WHERE token = ? AND expiry_date > ?
    """, (token, current_datetime), fetch=True)
    
    print(f"DEBUG - validate_session: Sessions trouvées pour token {token[:5]}...: {sessions}")
    
    if not sessions:
        print("DEBUG - validate_session: Aucune session valide trouvée")
        return None
    
    print(f"DEBUG - validate_session: Session valide, user_id = {sessions[0][0]}")
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
        # Supprimer la session avec syntaxe SQLite
        get_db("DELETE FROM sessions WHERE token = ?", (token,))
        try:
            log_activity(user_id, 'logout', 'auth', "Déconnexion")
        except Exception as e:
            print(f"Erreur lors de la journalisation de la déconnexion: {e}")
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
    users = get_db("SELECT * FROM USEUR WHERE ID = ?", (user_id,))
    if not users:
        return False
    
    # Vérifier si la table admin existe, sinon la créer
    get_db("""
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_user TEXT UNIQUE NOT NULL,
            FOREIGN KEY (id_user) REFERENCES USEUR(ID)
        )
    """)
    
    # Vérifier si l'utilisateur est déjà admin
    admin = get_db("SELECT * FROM admin WHERE id_user = ?", (user_id,))
    if admin:
        return True
    
    # Créer l'entrée admin avec syntaxe SQLite
    get_db("INSERT INTO admin (id_user) VALUES (?)", (user_id,))
    try:
        log_activity(user_id, 'promote', 'auth', "Promotion au rang d'administrateur")
    except Exception as e:
        print(f"Erreur lors de la journalisation de la promotion admin: {e}")
    
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
    users = get_db("SELECT * FROM USEUR WHERE ID = ?", (user_id,))
    if not users:
        return False
    
    # Vérifier si la table technicien existe, sinon la créer
    get_db("""
        CREATE TABLE IF NOT EXISTS technicien (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_user TEXT UNIQUE NOT NULL,
            specialite TEXT,
            FOREIGN KEY (id_user) REFERENCES USEUR(ID)
        )
    """)
    
    # Vérifier si l'utilisateur est déjà technicien
    tech = get_db("SELECT * FROM technicien WHERE id_user = ?", (user_id,))
    if tech:
        # Mettre à jour la spécialité si elle est fournie
        if speciality:
            get_db("UPDATE technicien SET specialite = ? WHERE id_user = ?", (speciality, user_id))
        return True
    
    # Créer l'entrée technicien avec syntaxe SQLite
    get_db("INSERT INTO technicien (id_user, specialite) VALUES (?, ?)", (user_id, speciality or 'Général'))
    try:
        log_activity(user_id, 'promote', 'auth', "Promotion au rang de technicien")
    except Exception as e:
        print(f"Erreur lors de la journalisation de la promotion technicien: {e}")
    
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
    users = get_db("SELECT * FROM USEUR WHERE ID = ?", (user_id,))
    if not users:
        return None
    
    user = users[0]
    
    # Récupérer le rôle avec gestion des tables inexistantes
    is_admin = False
    is_tech = False
    role = 'user'
    
    try:
        # Vérifier si la table admin existe avec sqlite_master
        admin_check = get_db("SELECT name FROM sqlite_master WHERE type='table' AND name='admin'")
        if admin_check:
            admin_result = get_db("SELECT * FROM admin WHERE id_user = ?", (user_id,))
            is_admin = bool(admin_result)
        
        # Vérifier si la table technicien existe avec sqlite_master
        tech_check = get_db("SELECT name FROM sqlite_master WHERE type='table' AND name='technicien'")
        if tech_check:
            tech_result = get_db("SELECT * FROM technicien WHERE id_user = ?", (user_id,))
            is_tech = bool(tech_result)
        
        role = 'admin' if is_admin else 'technician' if is_tech else 'user'
    except Exception as e:
        print(f"Erreur lors de la récupération du rôle pour JWT: {e}")
        # Continuer avec le rôle par défaut 'user'
    
    # Créer le payload
    payload = {
        'sub': user_id,
        'name': user[1],
        'email': user[5] if len(user) > 5 else None,
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