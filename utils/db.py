import mysql.connector
import json
import os
from datetime import datetime

# Variables globales pour la connexion à la base de données
_connection = None
_config = None

def load_config():
    """
    Charge la configuration depuis le fichier conf.conf
    
    Returns:
        dict: Configuration chargée ou dictionnaire vide en cas d'erreur
    """
    global _config
    
    # Si la configuration est déjà chargée, la retourner directement
    if _config is not None:
        return _config
    
    try:
        with open('config/conf.conf', 'r') as file:
            _config = json.load(file)
            return _config
    except FileNotFoundError:
        print("Le fichier de configuration n'a pas été trouvé.")
        return {}
    except json.JSONDecodeError:
        print("Erreur de décodage JSON dans le fichier de configuration.")
        return {}

def get_connection():
    """
    Établit ou récupère une connexion à la base de données
    
    Returns:
        mysql.connector.connection.MySQLConnection: Connexion à la base de données
    """
    global _connection
    
    # Si une connexion existe déjà et qu'elle est active, la retourner
    if _connection is not None and _connection.is_connected():
        return _connection
    
    # Charger la configuration
    config = load_config()
    
    # Déboguer les paramètres de connexion
    print(f"Tentative de connexion avec les paramètres:")
    print(f"- Host: {config.get('IP_db', 'localhost')}")
    print(f"- User: {config.get('user_db', 'root')}")
    print(f"- Database: {config.get('name_db', 'glpidb')}")
    
    # Établir une nouvelle connexion
    try:
        _connection = mysql.connector.connect(
            host=config.get('IP_db', 'localhost'),
            user=config.get('user_db', 'root'),
            password=config.get('password_db', ''),
            database=config.get('name_db', 'glpidb')
        )
        print(f"Connexion réussie à la base de données!")
        return _connection
    except mysql.connector.Error as err:
        print(f"Erreur de connexion à la base de données: {err}")
        # En cas d'échec, tenter une connexion sans spécifier de base de données
        try:
            _connection = mysql.connector.connect(
                host=config.get('IP_db', 'localhost'),
                user=config.get('user_db', 'root'),
                password=config.get('password_db', '')
            )
            print(f"Connexion réussie au serveur MySQL sans base de données!")
            return _connection
        except mysql.connector.Error as err:
            print(f"Erreur de connexion au serveur MySQL: {err}")
            raise

def get_db(query, params=None):
    """
    Exécute une requête SQL et retourne les résultats
    
    Args:
        query (str): Requête SQL à exécuter
        params (tuple/dict, optional): Paramètres pour la requête
    
    Returns:
        list: Résultats de la requête ou None si c'est une requête d'écriture
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        # Si la requête commence par SELECT, retourner les résultats
        if query.strip().upper().startswith('SELECT') or query.strip().upper().startswith('SHOW'):
            result = cursor.fetchall()
            return result
        else:
            conn.commit()
            return cursor.lastrowid if cursor.lastrowid else True
    except mysql.connector.Error as err:
        print(f"Erreur d'exécution de la requête SQL: {err}")
        print(f"Requête: {query}")
        print(f"Paramètres: {params}")
        conn.rollback()  # Annuler les changements en cas d'erreur
        raise
    finally:
        cursor.close()

def initialize_db():
    """
    Initialise la base de données avec les tables nécessaires si elles n'existent pas
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Vérifier si la base de données existe, sinon la créer
        config = load_config()
        db_name = config.get('name_db', 'glpidb')
        
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        cursor.execute(f"USE {db_name}")
        
        # Vérifier si la table USEUR existe et sa structure
        cursor.execute("SHOW TABLES LIKE 'USEUR'")
        if cursor.fetchone():
            print("Table USEUR existe déjà")
        else:
            # Création de la table USEUR si elle n'existe pas
            cursor.execute('''
            CREATE TABLE USEUR (
                id VARCHAR(36) PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                role VARCHAR(20) NOT NULL DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            print("Table USEUR créée avec succès")
        
        # Vérifier si la table activity_logs existe
        cursor.execute("SHOW TABLES LIKE 'activity_logs'")
        if cursor.fetchone():
            print("Table activity_logs existe déjà")
        else:
            # Création de la table activity_logs si elle n'existe pas
            cursor.execute('''
            CREATE TABLE activity_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id VARCHAR(36) NOT NULL,
                action_type VARCHAR(50) NOT NULL,
                module VARCHAR(50) NOT NULL,
                description TEXT,
                timestamp DATETIME NOT NULL,
                INDEX idx_user_id (user_id),
                INDEX idx_timestamp (timestamp)
            )
            ''')
            print("Table activity_logs créée avec succès")
            
        # Vérifier et créer les autres tables nécessaires
        from setup import set_up_database
        set_up_database()
        
        conn.commit()
        print("Base de données initialisée avec succès")
        
    except mysql.connector.Error as err:
        print(f"Erreur lors de l'initialisation de la base de données: {err}")
        conn.rollback()
    finally:
        cursor.close()

def ensure_activity_logs_table_exists():
    """
    Vérifie l'existence de la table activity_logs et la crée si elle n'existe pas
    
    Returns:
        bool: True si la table existe ou a été créée avec succès
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Vérifier si la table activity_logs existe
        cursor.execute("SHOW TABLES LIKE 'activity_logs'")
        if cursor.fetchone():
            # La table existe déjà
            cursor.close()
            return True
        
        # Création de la table activity_logs
        cursor.execute('''
        CREATE TABLE activity_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id VARCHAR(36) NOT NULL,
            action_type VARCHAR(50) NOT NULL,
            module VARCHAR(50) NOT NULL,
            description TEXT,
            timestamp DATETIME NOT NULL,
            INDEX idx_user_id (user_id),
            INDEX idx_timestamp (timestamp)
        )
        ''')
        conn.commit()
        print("Table activity_logs créée avec succès")
        cursor.close()
        return True
    
    except mysql.connector.Error as err:
        print(f"Erreur lors de la création de la table activity_logs: {err}")
        return False

def log_activity(user_id, action_type, module, description):
    """
    Enregistre une activité utilisateur dans les logs
    
    Args:
        user_id (str): ID de l'utilisateur
        action_type (str): Type d'action (create, update, delete, view, auth, etc.)
        module (str): Module concerné (tickets, inventory, activity, auth, etc.)
        description (str): Description de l'activité
    
    Returns:
        bool: True si l'enregistrement est réussi
    """
    try:
        # Vérifier et créer la table si nécessaire
        if not ensure_activity_logs_table_exists():
            print("Impossible de créer la table activity_logs. La journalisation est désactivée.")
            return False
        
        # Enregistrer l'activité
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        query = """
        INSERT INTO activity_logs (user_id, action_type, module, description, timestamp)
        VALUES (%s, %s, %s, %s, %s)
        """
        get_db(query, (user_id, action_type, module, description, timestamp))
        return True
    except Exception as e:
        print(f"Erreur lors de l'enregistrement de l'activité: {e}")
        return False