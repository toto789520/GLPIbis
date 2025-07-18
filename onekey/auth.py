import argon2
import hashlib
import secrets
import string
from datetime import datetime, timedelta
from utils.db_manager import get_db
import logging
app_logger = logging.getLogger("onekey.auth")
import re
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, HashingError, InvalidHash
import traceback

def validate_password(password):
    """
    Valide qu'un mot de passe respecte les critères de sécurité
    - Au moins 8 caractères
    - Au moins une majuscule
    - Au moins une minuscule  
    - Au moins un chiffre
    - Au moins un caractère spécial
    """
    app_logger.debug(f"Validation du mot de passe: {password[:5]}...")  # Log les 5 premiers caractères pour éviter de loguer le mot de passe complet
    # Vérifier la longueur minimale
    if not password or len(password) < 8:
        app_logger.debug("Validation du mot de passe échouée - Longueur insuffisante")
        return False
    
    # Vérifier la présence des différents types de caractères
    has_upper = re.search(r'[A-Z]', password) is not None
    has_lower = re.search(r'[a-z]', password) is not None
    has_digit = re.search(r'\d', password) is not None
    has_special = re.search(r'[!@#$%^&*(),.?":{}|<>]', password) is not None

    app_logger.debug(f"Validation du mot de passe - Majuscule: {has_upper}, Minuscule: {has_lower}, Chiffre: {has_digit}, Spécial: {has_special}")
    return has_upper and has_lower and has_digit and has_special

def generate_user_id():
    """Génère un ID utilisateur unique"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(40))

def generate_token():
    """Génère un token de session sécurisé"""
    return secrets.token_urlsafe(32)

def register_user(name, age, tel, email, password, role='user'):
    """
    Enregistre un nouveau utilisateur
    
    Args:
        name (str): Nom de l'utilisateur
        age (int): Âge de l'utilisateur
        tel (str): Téléphone de l'utilisateur
        email (str): Email de l'utilisateur
        password (str): Mot de passe de l'utilisateur
        role (str): Rôle de l'utilisateur ('admin', 'technician', 'user')
    
    Returns:
        str: ID de l'utilisateur créé ou None en cas d'erreur
    
    Raises:
        ValueError: Si l'email existe déjà ou si le mot de passe est invalide
    """
    try:
        # Vérifier si l'email existe déjà
        existing_user = get_db("SELECT ID FROM USEUR WHERE email = ?", (email,))
        if existing_user:
            raise ValueError("Un utilisateur avec cet email existe déjà")
          # Valider le mot de passe
        if not validate_password(password):
            app_logger.debug(f"Validation du mot de passe échouée pour {email}")
            raise ValueError("Le mot de passe ne respecte pas les critères de complexité")
        app_logger.debug(f"Validation du mot de passe réussie pour {email}")
        
        # Hasher le mot de passe
        ph = argon2.PasswordHasher()
        hashed_password = ph.hash(password)
        
        # Générer un ID utilisateur unique
        user_id = generate_user_id()
        
        # Créer l'utilisateur
        get_db("""
            INSERT INTO USEUR (ID, name, age, tel, password, email, creation_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, name, age, tel, hashed_password, email, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        # Créer les statistiques pour l'utilisateur
        get_db("""
            INSERT INTO state (id_user, tickets_created, tickets_participated, comments)
            VALUES (?, 0, 0, 0)
        """, (user_id,))
        
        # Assigner le rôle
        if role == 'admin':
            get_db("INSERT INTO admin (id_user) VALUES (?)", (user_id,))
        elif role == 'technician':
            get_db("INSERT INTO technicien (id_user) VALUES (?)", (user_id,))
        
        app_logger.info(f"INFO: Utilisateur {email} créé avec succès - ID: {user_id}")
        return user_id
        
    except Exception as e:
        app_logger.error(f"ERREUR - register_user: {str(e)}")
        raise e

# Créer une instance du hasher Argon2
ph = PasswordHasher()

def verify_password(password: str, hashed_password: str) -> bool:
    """
    Vérifie un mot de passe en utilisant Argon2
    """
    try:
        ph.verify(hashed_password, password)
        return True
    except (VerifyMismatchError, InvalidHash):
        return False
    except Exception as e:
        app_logger.error(f"Erreur lors de la vérification du mot de passe: {str(e)}")
        return False

# Alias pour compatibilité
validate_password_hash = verify_password

def login_user(email: str, password: str) -> dict:
    """
    Connecte un utilisateur avec email et mot de passe
    """
    try:
        app_logger.debug(f"DEBUG - login_user: Tentative de connexion pour {email}")
        
        # Chercher l'utilisateur par email
        users = get_db("SELECT ID, name, email, password FROM USEUR WHERE email = ?", (email,))
        app_logger.debug(f"DEBUG - Utilisateur trouvé pour {email}: {users}")
        
        if not users:
            app_logger.debug("DEBUG - login_user: Aucun utilisateur trouvé")
            return {
                'status': 'error',
                'message': 'Email ou mot de passe incorrect',
                'user_id': None,
                'username': None,
                'token': None
            }
        
        user = users[0]
        user_id, username, user_email, hashed_password = user
        
        # Vérifier le mot de passe
        if not verify_password(password, hashed_password):
            app_logger.debug("DEBUG - login_user: Mot de passe incorrect")
            return {
                'status': 'error',
                'message': 'Email ou mot de passe incorrect',
                'user_id': None,
                'username': None,
                'token': None
            }
        
        # Générer un token de session
        token = secrets.token_urlsafe(32)
        app_logger.debug(f"DEBUG - login_user: Génération d'un nouveau token: {token[:5]}...")
        
        # Créer la session en base
        expiry_date = (datetime.now() + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:%S")
        try:
            get_db("INSERT INTO sessions (user_id, token, expiry_date) VALUES (?, ?, ?)",
                   (user[0], token, expiry_date))
            app_logger.debug(f"DEBUG - login_user: Session créée avec succès pour {email}, token: {token[:5]}...")
        except Exception as session_error:
            app_logger.error(f"ERREUR - login_user: Erreur lors de la création de la session: {str(session_error)}")
            raise Exception(f"Erreur lors de la création de la session: {str(session_error)}")
        
        return {
            'status': 'success',
            'message': 'Connexion réussie',
            'token': token,
            'user_id': user_id,
            'email': email
        }
            
    except Exception as e:
        app_logger.error(f"ERREUR - login_user: Erreur lors de la gestion de session: {str(e)}")
        raise Exception({'status': 'error', 'message': f'Erreur de connexion: {str(e)}'})

def validate_session(token):
    """
    Valide un token de session
    
    Args:
        token (str): Token de session à valider
    
    Returns:
        str|bool: user_id si la session est valide, False sinon
    """
    try:
        if not token:
            return False
        
        # Rechercher la session
        sessions = get_db("""
            SELECT user_id, expiry_date FROM sessions 
            WHERE token = ?
        """, (token,))
        
        app_logger.debug(f"DEBUG - validate_session: Sessions trouvées pour token {token[:5]}...: {sessions}")
        
        if not sessions:
            app_logger.debug("DEBUG - validate_session: Aucune session trouvée pour ce token")
            return False
        
        session = sessions[0]
        user_id, expiry_date_str = session
        
        # Vérifier si la session n'a pas expiré
        try:
            expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d %H:%M:%S")
            if datetime.now() > expiry_date:
                app_logger.debug("DEBUG - validate_session: Session expirée")
                # Supprimer la session expirée
                get_db("DELETE FROM sessions WHERE token = ?", (token,))
                return False
        except ValueError as date_err:
            app_logger.error(f"Erreur de format de date: {str(date_err)}")
            return False
        
        app_logger.debug(f"DEBUG - validate_session: Session valide, user_id = {user_id}")
        return user_id
        
    except Exception as e:
        app_logger.error(f"ERREUR - validate_session: {str(e)}")
        return False

def logout_user(token):
    """
    Déconnecte un utilisateur en supprimant sa session
    
    Args:
        token (str): Token de session à supprimer
    
    Returns:
        bool: True si la déconnexion est réussie
    """
    try:
        if not token:
            return False
        
        # Supprimer la session
        get_db("DELETE FROM sessions WHERE token = ?", (token,))
        app_logger.debug(f"Session supprimée pour token: {token[:5]}...")
        
        return True
        
    except Exception as e:
        app_logger.error(f"ERREUR - logout_user: {str(e)}")
        return False

def cleanup_expired_sessions():
    """
    Nettoie les sessions expirées de la base de données
    
    Returns:
        int: Nombre de sessions supprimées
    """
    try:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Compter les sessions expirées
        expired_sessions = get_db("""
            SELECT COUNT(*) FROM sessions 
            WHERE expiry_date < ?
        """, (current_time,))
        
        count = expired_sessions[0][0] if expired_sessions else 0
        
        # Supprimer les sessions expirées
        get_db("DELETE FROM sessions WHERE expiry_date < ?", (current_time,))
        
        if count > 0:
            app_logger.info(f"Nettoyage: {count} sessions expirées supprimées")
        
        return count
        
    except Exception as e:
        app_logger.error(f"ERREUR - cleanup_expired_sessions: {str(e)}")
        return 0