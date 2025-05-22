import os
import json
import threading
from datetime import datetime
import sqlite3

try:
    import pymysql
except ImportError:
    pymysql = None

_thread_local = threading.local()

class DBManager:
    def __init__(self, db_type='sqlite', mysql_params=None):
        self.db_type = db_type.lower()
        self.mysql_params = mysql_params or {}
        self.connection = None

    def get_connection(self):
        if self.db_type == 'sqlite':
            # Une meilleure approche pour SQLite dans un environnement multi-thread
            # Utiliser check_same_thread=False avec précaution
            if not hasattr(_thread_local, 'connection'):
                db_path = os.path.join(os.getcwd(), 'database.sqlite')
                _thread_local.connection = sqlite3.connect(db_path, check_same_thread=False, timeout=30)
                # Activer le suivi des clés étrangères
                _thread_local.connection.execute("PRAGMA foreign_keys = ON")
                # Activer un timeout plus long pour éviter les verrous de base de données
                _thread_local.connection.execute("PRAGMA busy_timeout = 30000")
            return _thread_local.connection
        elif self.db_type == 'mysql':
            # Pour MySQL, vérifier si la connexion est toujours active
            if self.connection is None:
                if pymysql is None:
                    raise ImportError("pymysql is required for MySQL support")
                self.connection = pymysql.connect(
                    host=self.mysql_params.get('host', 'localhost'),
                    port=int(self.mysql_params.get('port', 3306)),
                    user=self.mysql_params.get('user', 'root'),
                    password=self.mysql_params.get('password', ''),
                    database=self.mysql_params.get('db', 'glpidb'),
                    charset='utf8mb4',
                    cursorclass=pymysql.cursors.DictCursor,
                    autocommit=True
                )
            else:
                # Vérifier si la connexion est toujours active
                try:
                    self.connection.ping(reconnect=True)
                except:
                    # Si la connexion est perdue, se reconnecter
                    self.connection = pymysql.connect(
                        host=self.mysql_params.get('host', 'localhost'),
                        port=int(self.mysql_params.get('port', 3306)),
                        user=self.mysql_params.get('user', 'root'),
                        password=self.mysql_params.get('password', ''),
                        database=self.mysql_params.get('db', 'glpidb'),
                        charset='utf8mb4',
                        cursorclass=pymysql.cursors.DictCursor,
                        autocommit=True
                    )
            return self.connection
        else:
            raise ValueError("Unsupported database type")

    def execute_query(self, query, params=None, fetch=False):
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            if fetch:
                result = cursor.fetchall()
                return result
            else:
                if self.db_type == 'sqlite':
                    conn.commit()
                return cursor.lastrowid if cursor.lastrowid else True
        except Exception as e:
            if self.db_type == 'sqlite':
                conn.rollback()
            raise e
        finally:
            cursor.close()

    def initialize_database(self):
        if self.db_type == 'sqlite':
            db_path = os.path.join(os.getcwd(), 'database.sqlite')
            if not os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                conn.execute("PRAGMA foreign_keys = ON")
                conn.close()
            self.create_tables()
        elif self.db_type == 'mysql':
            # Create database if not exists
            host = self.mysql_params.get('host', 'localhost')
            port = int(self.mysql_params.get('port', 3306))
            user = self.mysql_params.get('user', 'root')
            password = self.mysql_params.get('password', '')
            database = self.mysql_params.get('db', 'glpidb')
            try:
                temp_conn = pymysql.connect(host=host, port=port, user=user, password=password)
                with temp_conn.cursor() as cursor:
                    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database}")
                temp_conn.close()
                self.connection = pymysql.connect(host=host, port=port, user=user, password=password, database=database)
                self.create_tables()
            except Exception as e:
                raise RuntimeError(f"MySQL initialization error: {e}")
        else:
            raise ValueError("Unsupported database type")

    def create_tables(self):
        if self.db_type == 'sqlite':
            # SQLite schema
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS USEUR (
                    ID TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    age INTEGER,
                    tel TEXT,
                    hashed_password TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    dete_de_creation TEXT,
                    derniere_connexion TEXT,
                    role TEXT DEFAULT 'user'
                )
            """)
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    token TEXT NOT NULL UNIQUE,
                    expiry_date TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES USEUR(ID) ON DELETE CASCADE
                )
            """)
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS state (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_user TEXT NOT NULL,
                    tiqué_créer INTEGER DEFAULT 0,
                    tiqué_partisipé INTEGER DEFAULT 0,
                    comm INTEGER DEFAULT 0,
                    FOREIGN KEY (id_user) REFERENCES USEUR(ID) ON DELETE CASCADE
                )
            """)
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS tiqué (
                    ID_tiqué INTEGER PRIMARY KEY AUTOINCREMENT,
                    ID_user TEXT NOT NULL,
                    titre TEXT NOT NULL,
                    date_open TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    date_close TIMESTAMP,
                    ID_technicien TEXT,
                    description TEXT,
                    open INTEGER DEFAULT 1,
                    tag TEXT,
                    gravite INTEGER DEFAULT 5,
                    FOREIGN KEY (ID_user) REFERENCES USEUR(ID),
                    FOREIGN KEY (ID_technicien) REFERENCES USEUR(ID)
                )
            """)
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS commentaires (
                    ID_comm INTEGER PRIMARY KEY AUTOINCREMENT,
                    ID_tiqué INTEGER NOT NULL,
                    ID_user TEXT NOT NULL,
                    contenur TEXT,
                    date_comm TIMESTAMP NOT NULL,
                    is_staff INTEGER DEFAULT 0,
                    FOREIGN KEY (ID_tiqué) REFERENCES tiqué(ID_tiqué) ON DELETE CASCADE,
                    FOREIGN KEY (ID_user) REFERENCES USEUR(ID)
                )
            """)
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS admin (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_user TEXT NOT NULL UNIQUE,
                    FOREIGN KEY (id_user) REFERENCES USEUR(ID) ON DELETE CASCADE
                )
            """)
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS technicien (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_user TEXT NOT NULL UNIQUE,
                    specialite TEXT DEFAULT 'Général',
                    FOREIGN KEY (id_user) REFERENCES USEUR(ID) ON DELETE CASCADE
                )
            """)
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS activity_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    module TEXT NOT NULL,
                    description TEXT,
                    timestamp DATETIME NOT NULL
                )
            """)
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS inventory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    category TEXT,
                    status TEXT DEFAULT 'available',
                    location TEXT,
                    serial_number TEXT UNIQUE,
                    qr_code TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS categorie (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom TEXT NOT NULL UNIQUE,
                    description TEXT,
                    icone TEXT DEFAULT 'fas fa-box',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS sous_categorie (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom TEXT NOT NULL,
                    id_categorie INTEGER NOT NULL,
                    description TEXT,
                    FOREIGN KEY (id_categorie) REFERENCES categorie(id) ON DELETE CASCADE,
                    UNIQUE(nom, id_categorie)
                )
            """)
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS sous_sous_categorie (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom TEXT NOT NULL,
                    id_sous_categorie INTEGER NOT NULL,
                    description TEXT,
                    FOREIGN KEY (id_sous_categorie) REFERENCES sous_categorie(id) ON DELETE CASCADE,
                    UNIQUE(nom, id_sous_categorie)
                )
            """)
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS localisation (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    batiment TEXT NOT NULL,
                    etage TEXT,
                    salle TEXT,
                    description TEXT
                )
            """)
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS materiel (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom TEXT NOT NULL,
                    categorie INTEGER NOT NULL,
                    sous_categorie INTEGER NOT NULL,
                    sous_sous_categorie INTEGER NOT NULL,
                    date_creation TEXT DEFAULT CURRENT_TIMESTAMP,
                    qr_code TEXT UNIQUE,
                    id_localisation INTEGER,
                    FOREIGN KEY (categorie) REFERENCES categorie(id),
                    FOREIGN KEY (sous_categorie) REFERENCES sous_categorie(id),
                    FOREIGN KEY (sous_sous_categorie) REFERENCES sous_sous_categorie(id),
                    FOREIGN KEY (id_localisation) REFERENCES localisation(id)
                )
            """)
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS ticket_materiel (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_ticket INTEGER NOT NULL,
                    id_materiel INTEGER NOT NULL,
                    date_association TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (id_ticket) REFERENCES tiqué(ID_tiqué),
                    FOREIGN KEY (id_materiel) REFERENCES materiel(id)
                )
            """)
            # Création de la table pret avec la syntaxe appropriée selon le type de base de données
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS pret (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_materiel INTEGER NOT NULL,
                    id_emprunteur VARCHAR(36) NOT NULL,
                    date_pret DATETIME DEFAULT CURRENT_TIMESTAMP,
                    date_retour_prevue DATETIME NOT NULL,
                    date_retour DATETIME,
                    statut VARCHAR(50) DEFAULT 'en_cours',
                    notes TEXT,
                    FOREIGN KEY (id_materiel) REFERENCES materiel(id) ON DELETE CASCADE,
                    FOREIGN KEY (id_emprunteur) REFERENCES USEUR(ID) ON DELETE CASCADE
                )
            """)
            # Création de la table intervention avec la syntaxe appropriée selon le type de base de données
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS intervention (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_materiel INTEGER NOT NULL,
                    id_technicien VARCHAR(36) NOT NULL,
                    type VARCHAR(100) NOT NULL,
                    description TEXT,
                    date_debut DATETIME DEFAULT CURRENT_TIMESTAMP,
                    date_fin DATETIME,
                    statut VARCHAR(50) DEFAULT 'en_cours',
                    FOREIGN KEY (id_materiel) REFERENCES materiel(id) ON DELETE CASCADE
                )
            """)
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS tiqué (
                    ID_tiqué INTEGER PRIMARY KEY AUTOINCREMENT,
                    ID_user TEXT NOT NULL,
                    titre TEXT NOT NULL,
                    date_open TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    date_close TIMESTAMP,
                    ID_technicien TEXT,
                    description TEXT,
                    open INTEGER DEFAULT 1,
                    tag TEXT,
                    gravite INTEGER DEFAULT 5,
                    FOREIGN KEY (ID_user) REFERENCES USEUR(ID),
                    FOREIGN KEY (ID_technicien) REFERENCES USEUR(ID)
                )
            """)
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS commentaires (
                    ID_comm INTEGER PRIMARY KEY AUTOINCREMENT,
                    ID_tiqué INTEGER NOT NULL,
                    ID_user TEXT NOT NULL,
                    contenur TEXT,
                    date_comm TIMESTAMP NOT NULL,
                    is_staff INTEGER DEFAULT 0,
                    FOREIGN KEY (ID_tiqué) REFERENCES tiqué(ID_tiqué) ON DELETE CASCADE,
                    FOREIGN KEY (ID_user) REFERENCES USEUR(ID)
                )
            """)
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS admin (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_user TEXT NOT NULL UNIQUE,
                    FOREIGN KEY (id_user) REFERENCES USEUR(ID) ON DELETE CASCADE
                )
            """)
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS technicien (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_user TEXT NOT NULL UNIQUE,
                    specialite TEXT DEFAULT 'Général',
                    FOREIGN KEY (id_user) REFERENCES USEUR(ID) ON DELETE CASCADE
                )
            """)
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS activity_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    module TEXT NOT NULL,
                    description TEXT,
                    timestamp DATETIME NOT NULL
                )
            """)
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS inventory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    category TEXT,
                    status TEXT DEFAULT 'available',
                    location TEXT,
                    serial_number TEXT UNIQUE,
                    qr_code TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS categorie (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom TEXT NOT NULL UNIQUE,
                    description TEXT,
                    icone TEXT DEFAULT 'fas fa-box',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS sous_categorie (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom TEXT NOT NULL,
                    id_categorie INTEGER NOT NULL,
                    description TEXT,
                    FOREIGN KEY (id_categorie) REFERENCES categorie(id) ON DELETE CASCADE,
                    UNIQUE(nom, id_categorie)
                )
            """)
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS sous_sous_categorie (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom TEXT NOT NULL,
                    id_sous_categorie INTEGER NOT NULL,
                    description TEXT,
                    FOREIGN KEY (id_sous_categorie) REFERENCES sous_categorie(id) ON DELETE CASCADE,
                    UNIQUE(nom, id_sous_categorie)
                )
            """)
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS localisation (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    batiment TEXT NOT NULL,
                    etage TEXT,
                    salle TEXT,
                    description TEXT
                )
            """)
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS materiel (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom TEXT NOT NULL,
                    categorie INTEGER NOT NULL,
                    sous_categorie INTEGER NOT NULL,
                    sous_sous_categorie INTEGER NOT NULL,
                    date_creation TEXT DEFAULT CURRENT_TIMESTAMP,
                    qr_code TEXT UNIQUE,
                    id_localisation INTEGER,
                    FOREIGN KEY (categorie) REFERENCES categorie(id),
                    FOREIGN KEY (sous_categorie) REFERENCES sous_categorie(id),
                    FOREIGN KEY (sous_sous_categorie) REFERENCES sous_sous_categorie(id),
                    FOREIGN KEY (id_localisation) REFERENCES localisation(id)
                )
            """)
        elif self.db_type == 'mysql':
            # MySQL schema
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS USEUR (
                    ID VARCHAR(36) PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    age INT,
                    tel VARCHAR(20),
                    hashed_password VARCHAR(255) NOT NULL,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    dete_de_creation DATETIME,
                    derniere_connexion DATETIME,
                    role VARCHAR(50) DEFAULT 'user'
                )
            """)
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id VARCHAR(36) NOT NULL,
                    token VARCHAR(64) NOT NULL UNIQUE,
                    expiry_date DATETIME NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES USEUR(ID) ON DELETE CASCADE
                )
            """)
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS state (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    id_user VARCHAR(36) NOT NULL,
                    tiqué_créer INT DEFAULT 0,
                    tiqué_partisipé INT DEFAULT 0,
                    comm INT DEFAULT 0,
                    FOREIGN KEY (id_user) REFERENCES USEUR(ID) ON DELETE CASCADE
                )
            """)
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS tiqué (
                    ID_tiqué VARCHAR(36) PRIMARY KEY,
                    ID_user VARCHAR(36) NOT NULL,
                    titre VARCHAR(255) NOT NULL,
                    date_open DATETIME NOT NULL,
                    date_close DATETIME,
                    ID_technicien VARCHAR(36),
                    description TEXT,
                    open BOOLEAN DEFAULT TRUE,
                    tag VARCHAR(50),
                    gravite INT DEFAULT 5,
                    FOREIGN KEY (ID_user) REFERENCES USEUR(ID),
                    FOREIGN KEY (ID_technicien) REFERENCES USEUR(ID)
                )
            """)
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS commentaires (
                    ID_comm VARCHAR(36) PRIMARY KEY,
                    ID_tiqué VARCHAR(36) NOT NULL,
                    ID_user VARCHAR(36) NOT NULL,
                    contenur TEXT,
                    date_comm DATETIME NOT NULL,
                    is_staff BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (ID_tiqué) REFERENCES tiqué(ID_tiqué) ON DELETE CASCADE,
                    FOREIGN KEY (ID_user) REFERENCES USEUR(ID)
                )
            """)
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS admin (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    id_user VARCHAR(36) NOT NULL UNIQUE,
                    FOREIGN KEY (id_user) REFERENCES USEUR(ID) ON DELETE CASCADE
                )
            """)
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS technicien (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    id_user VARCHAR(36) NOT NULL UNIQUE,
                    specialite VARCHAR(100),
                    FOREIGN KEY (id_user) REFERENCES USEUR(ID) ON DELETE CASCADE
                )
            """)
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS activity_logs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id VARCHAR(36),
                    action VARCHAR(50) NOT NULL,
                    module VARCHAR(50) NOT NULL,
                    description TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES USEUR(ID) ON DELETE SET NULL
                )
            """)
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS inventory (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    category VARCHAR(100),
                    status VARCHAR(50) DEFAULT 'available',
                    location VARCHAR(255),
                    serial_number VARCHAR(255) UNIQUE,
                    qr_code VARCHAR(255) UNIQUE,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS categorie (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nom VARCHAR(255) NOT NULL UNIQUE,
                    description TEXT,
                    icone VARCHAR(255) DEFAULT 'fas fa-box',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS sous_categorie (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nom VARCHAR(255) NOT NULL,
                    id_categorie INT NOT NULL,
                    description TEXT,
                    FOREIGN KEY (id_categorie) REFERENCES categorie(id) ON DELETE CASCADE,
                    UNIQUE KEY nom_categorie (nom, id_categorie)
                )
            """)
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS sous_sous_categorie (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nom VARCHAR(255) NOT NULL,
                    id_sous_categorie INT NOT NULL,
                    description TEXT,
                    FOREIGN KEY (id_sous_categorie) REFERENCES sous_categorie(id) ON DELETE CASCADE,
                    UNIQUE KEY nom_sous_categorie (nom, id_sous_categorie)
                )
            """)
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS localisation (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    batiment VARCHAR(255) NOT NULL,
                    etage VARCHAR(50),
                    salle VARCHAR(255),
                    description TEXT
                )
            """)
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS materiel (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nom VARCHAR(255) NOT NULL,
                    categorie INT NOT NULL,
                    sous_categorie INT NOT NULL,
                    sous_sous_categorie INT NOT NULL,
                    date_creation DATETIME DEFAULT CURRENT_TIMESTAMP,
                    qr_code VARCHAR(50) UNIQUE,
                    id_localisation INT,
                    FOREIGN KEY (categorie) REFERENCES categorie(id),
                    FOREIGN KEY (sous_categorie) REFERENCES sous_categorie(id),
                    FOREIGN KEY (sous_sous_categorie) REFERENCES sous_sous_categorie(id),
                    FOREIGN KEY (id_localisation) REFERENCES localisation(id)
                )
            """)
            # Création de la table pret avec la syntaxe appropriée selon le type de base de données
            self.execute_query("""                CREATE TABLE IF NOT EXISTS pret (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_materiel INTEGER NOT NULL,
                    id_emprunteur VARCHAR(36) NOT NULL,
                    date_pret DATETIME DEFAULT CURRENT_TIMESTAMP,
                    date_retour_prevue DATETIME NOT NULL,
                    date_retour DATETIME,
                    statut VARCHAR(50) DEFAULT 'en_cours',
                    notes TEXT,
                    FOREIGN KEY (id_materiel) REFERENCES materiel(id) ON DELETE CASCADE,
                    FOREIGN KEY (id_emprunteur) REFERENCES USEUR(ID) ON DELETE CASCADE
                )
            """)
            # Création de la table intervention avec la syntaxe appropriée selon le type de base de données
            self.execute_query("""                CREATE TABLE IF NOT EXISTS intervention (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_materiel INTEGER NOT NULL,
                    id_technicien VARCHAR(36) NOT NULL,
                    type VARCHAR(100) NOT NULL,
                    description TEXT,
                    date_debut DATETIME DEFAULT CURRENT_TIMESTAMP,
                    date_fin DATETIME,
                    statut VARCHAR(50) DEFAULT 'en_cours',
                    FOREIGN KEY (id_materiel) REFERENCES materiel(id) ON DELETE CASCADE
                )
            """)

    def verify_table_structure(self):
        # Implement verification and update of table structure if needed
        # For SQLite, check columns and add missing ones
        if self.db_type == 'sqlite':
            try:
                columns = self.execute_query("PRAGMA table_info(USEUR)", fetch=True)
                column_names = [col[1] for col in columns]
                if 'age' not in column_names:
                    self.execute_query("ALTER TABLE USEUR ADD COLUMN age INTEGER")
                if 'tel' not in column_names:
                    self.execute_query("ALTER TABLE USEUR ADD COLUMN tel TEXT")
                if 'role' not in column_names:
                    self.execute_query("ALTER TABLE USEUR ADD COLUMN role TEXT DEFAULT 'user'")
                if 'derniere_connexion' not in column_names:
                    self.execute_query("ALTER TABLE USEUR ADD COLUMN derniere_connexion TEXT")
            except Exception as e:
                print(f"Error verifying SQLite table structure: {e}")
        elif self.db_type == 'mysql':
            try:
                columns = self.execute_query("""
                    SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = 'USEUR'
                """, fetch=True)
                column_names = [col['COLUMN_NAME'] for col in columns]
                if 'age' not in column_names:
                    self.execute_query("ALTER TABLE USEUR ADD COLUMN age INT")
                if 'tel' not in column_names:
                    self.execute_query("ALTER TABLE USEUR ADD COLUMN tel VARCHAR(20)")
                if 'role' not in column_names:
                    self.execute_query("ALTER TABLE USEUR ADD COLUMN role VARCHAR(50) DEFAULT 'user'")
            except Exception as e:
                print(f"Error verifying MySQL table structure: {e}")

    def test_connection(self):
        """
        Teste la connexion à la base de données sans effectuer de modifications.
        Renvoie un tuple (succès, message) où succès est un booléen indiquant si le test est réussi,
        et message est un message explicatif en cas d'échec.
        """
        try:
            if self.db_type == 'sqlite':
                db_path = os.path.join(os.getcwd(), 'database.sqlite')
                if os.path.exists(db_path):
                    # Vérifier que le fichier est accessible en lecture/écriture
                    if not os.access(db_path, os.R_OK | os.W_OK):
                        return False, f"Le fichier de base de données existe mais n'est pas accessible en lecture/écriture: {db_path}"
                else:
                    # Vérifier que le répertoire est accessible en écriture
                    parent_dir = os.getcwd()
                    if not os.access(parent_dir, os.W_OK):
                        return False, f"Le répertoire n'est pas accessible en écriture: {parent_dir}"
                    
                # Tester la connexion SQLite
                try:
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    cursor.close()
                    conn.close()
                    return True, "Connexion SQLite réussie"
                except sqlite3.Error as e:
                    return False, f"Erreur de connexion SQLite: {str(e)}"
                    
            elif self.db_type == 'mysql':
                if pymysql is None:
                    return False, "Module pymysql manquant pour la connexion MySQL. Installez-le avec 'pip install pymysql'"
                    
                host = self.mysql_params.get('host', 'localhost')
                port = int(self.mysql_params.get('port', 3306))
                user = self.mysql_params.get('user', 'root')
                password = self.mysql_params.get('password', '')
                database = self.mysql_params.get('db', 'glpidb')
                
                # D'abord, tester la connexion sans la base de données
                try:
                    temp_conn = pymysql.connect(host=host, port=port, user=user, password=password)
                    temp_conn.close()
                except Exception as e:
                    return False, f"Erreur de connexion au serveur MySQL: {str(e)}"
                    
                # Ensuite, tester la connexion avec la base de données
                try:
                    conn = pymysql.connect(host=host, port=port, user=user, password=password, database=database)
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    cursor.close()
                    conn.close()
                    return True, "Connexion MySQL réussie"
                except pymysql.Error as e:
                    error_code = e.args[0]
                    if error_code == 1049:  # Base de données inexistante
                        return False, f"La base de données '{database}' n'existe pas. Elle sera créée lors de l'initialisation."
                    elif error_code == 1045:  # Accès refusé
                        return False, f"Accès refusé pour l'utilisateur '{user}'. Vérifiez vos identifiants."
                    else:
                        return False, f"Erreur de connexion MySQL: {str(e)}"
            else:
                return False, f"Type de base de données non pris en charge: {self.db_type}"
                
        except Exception as e:
            return False, f"Erreur lors du test de connexion: {str(e)}"

    def close_connection(self):
        if self.db_type == 'mysql' and self.connection:
            self.connection.close()
            self.connection = None

# Singleton instance for app usage
db_manager = None

def init_db_manager(db_type='sqlite', mysql_params=None):
    """
    Initialise le gestionnaire de base de données avec le type de base de données spécifié
    et les paramètres MySQL si nécessaire. Effectue un test de connexion avant l'initialisation.
    
    Args:
        db_type (str): Type de base de données ('sqlite' ou 'mysql')
        mysql_params (dict, optional): Paramètres de connexion MySQL
        
    Returns:
        DBManager: Instance du gestionnaire de base de données
        
    Raises:
        RuntimeError: Si le test de connexion ou l'initialisation échoue
    """
    global db_manager
    
    # Créer une instance temporaire pour tester la connexion
    temp_manager = DBManager(db_type, mysql_params)
    success, message = temp_manager.test_connection()
    
    if not success:
        # Si le test échoue mais qu'il s'agit de l'absence de la base de données MySQL,
        # on peut continuer car initialize_database() va la créer
        if db_type == 'mysql' and "n'existe pas" in message:
            print(f"Info: {message}")
        else:
            # Pour d'autres erreurs, lever une exception
            raise RuntimeError(f"Erreur lors du test de connexion à la base de données: {message}")
    
    # Créer l'instance finale
    db_manager = temp_manager
    
    try:
        # Initialiser la base de données (création des tables)
        db_manager.initialize_database()
        
        # Vérifier et mettre à jour la structure des tables si nécessaire
        db_manager.verify_table_structure()
        
        return db_manager
    except Exception as e:
        error_msg = str(e)
        if db_type == 'mysql':
            if "Access denied" in error_msg:
                raise RuntimeError(f"Accès refusé à la base de données MySQL. Vérifiez vos identifiants.")
            elif "Can't connect" in error_msg:
                raise RuntimeError(f"Impossible de se connecter au serveur MySQL. Vérifiez l'hôte et le port.")
        
        raise RuntimeError(f"Erreur lors de l'initialisation de la base de données: {error_msg}")

def get_db(query=None, params=None, fetch=True):
    """
    Fonction utilitaire pour exécuter des requêtes sur la base de données.
    
    Args:
        query (str, optional): La requête SQL à exécuter. Si None, renvoie juste l'instance de db_manager.
        params (tuple, optional): Les paramètres à passer à la requête.
        fetch (bool, optional): Si True, récupère et renvoie les résultats.
        
    Returns:
        Les résultats de la requête si fetch=True, sinon le code de retour de la requête.
    """
    if query == 'connect':
        # Pour la compatibilité avec l'ancien code qui utilise une connexion directe
        return db_manager.get_connection()
        
    if query is None:
        return db_manager
        
    return db_manager.execute_query(query, params, fetch)

def log_activity(user_id, action_type, module, description):
    """
    Enregistre une activité dans les logs.
    
    Args:
        user_id (str): L'ID de l'utilisateur qui effectue l'action.
        action_type (str): Le type d'action ('create', 'update', 'delete', etc.).
        module (str): Le module concerné ('ticket', 'inventory', 'auth', etc.).
        description (str): Description de l'action.
        
    Returns:
        bool: True si l'activité a été enregistrée avec succès, False sinon.
    """
    try:
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        query = """
        INSERT INTO activity_logs (user_id, action_type, module, description, timestamp)
        VALUES (?, ?, ?, ?, ?)
        """
        
        db_manager.execute_query(query, (user_id, action_type, module, description, timestamp))
        return True
    except Exception as e:
        print(f"Erreur lors de l'enregistrement de l'activité: {str(e)}")
        return False

def load_config():
    """
    Charge et renvoie la configuration depuis le fichier de configuration.
    Si le fichier n'existe pas ou est illisible, renvoie une configuration par défaut.
    
    Returns:
        dict: La configuration chargée
    """
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'conf.conf')
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        print(f"Erreur lors du chargement de la configuration: {str(e)}")
        
    # Configuration par défaut en cas d'échec
    return {
        "db_type": "sqlite",
        "company_name": "GLPIbis",
        "app_settings": {
            "session_duration_hours": 24,
            "debug_mode": True,
            "log_level": "INFO"
        }
    }
