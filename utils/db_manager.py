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
        self.db_type = db_type
        self.mysql_params = mysql_params or {}
        self.connection = None
        
        # Importer le logger ici pour éviter les imports circulaires
        try:
            from .logger import app_logger
            self.logger = app_logger
        except ImportError:
            import logging
            self.logger = logging.getLogger(__name__)

    def get_connection(self):
        if self.db_type == 'sqlite':
            # Une meilleure approche pour SQLite dans un environnement multi-thread
            # Utiliser check_same_thread=False avec précaution
            if not hasattr(_thread_local, 'connection'):
                db_path = os.path.join(os.getcwd(), 'glpibis.db')
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

    def execute_query(self, query, params=None, return_results=True):
        """Exécute une requête SQL avec gestion d'erreur améliorée"""
        try:
            # Importer le logger ici pour éviter les imports circulaires
            try:
                from .logger import get_logger
                logger = get_logger()
            except ImportError:
                import logging
                logger = logging.getLogger(__name__)
            if self.db_type == 'sqlite':
                import sqlite3
                
                # S'assurer que le répertoire existe
                db_path = os.path.join(os.getcwd(), 'glpibis.db')
                
                with sqlite3.connect(db_path) as conn:
                    cursor = conn.cursor()
                    if params:
                        result = cursor.execute(query, params)
                    else:
                        result = cursor.execute(query)
                    
                    if query.strip().upper().startswith(('SELECT', 'PRAGMA')):
                        return cursor.fetchall()
                    else:
                        conn.commit()
                        return True
                        
            elif self.db_type == 'mysql':
                # Pour MySQL, utiliser la connexion existante
                conn = self.get_connection()
                with conn.cursor() as cursor:
                    if params:
                        cursor.execute(query, params)
                    else:
                        cursor.execute(query)
                    
                    if query.strip().upper().startswith('SELECT'):
                        return cursor.fetchall()
                    else:
                        conn.commit()
                        return True
                
        except Exception as e:
            try:
                from .logger import get_logger
                logger = get_logger()
            except ImportError:
                import logging
                logger = logging.getLogger(__name__)
            logger.error(f"Erreur lors de l'exécution de la requête: {str(e)}")
            logger.error(f"Requête: {query}")
            if params:
                logger.error(f"Paramètres: {params}")
            return False

    def initialize_database(self):
        if self.db_type == 'sqlite':
            db_path = os.path.join(os.getcwd(), 'glpibis.db')
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
        """Crée toutes les tables nécessaires"""
        try:
            if self.db_type == 'sqlite':
                # Table des utilisateurs avec la colonne password
                self.execute_query("""
                    CREATE TABLE IF NOT EXISTS USEUR (
                        ID TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        age INTEGER,
                        tel TEXT,
                        password TEXT NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        role TEXT DEFAULT 'user'
                    )
                """)
                
                # Table des sessions avec les bonnes colonnes
                self.execute_query("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        token TEXT UNIQUE NOT NULL,
                        creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expiry_date TIMESTAMP NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES USEUR(ID)
                    )
                """)
                
                # Table des tickets avec ID_technicien
                success = self.execute_query("""
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
                        gravite INTEGER DEFAULT 1,
                        FOREIGN KEY (ID_user) REFERENCES USEUR(ID),
                        FOREIGN KEY (ID_technicien) REFERENCES USEUR(ID)
                    )
                """)
                if not success:
                    raise Exception("Échec de la création de la table tiqué")
                
                # Table des administrateurs
                success = self.execute_query("""
                    CREATE TABLE IF NOT EXISTS admin (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        id_user TEXT UNIQUE NOT NULL,
                        FOREIGN KEY (id_user) REFERENCES USEUR(ID)
                    )
                """)
                if not success:
                    raise Exception("Échec de la création de la table admin")
                
                # Table des techniciens
                success = self.execute_query("""
                    CREATE TABLE IF NOT EXISTS technicien (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        id_user TEXT UNIQUE NOT NULL,
                        specialite TEXT,
                        FOREIGN KEY (id_user) REFERENCES USEUR(ID)
                    )
                """)
                if not success:
                    raise Exception("Échec de la création de la table technicien")
                
                # Table des statistiques utilisateur
                success = self.execute_query("""
                    CREATE TABLE IF NOT EXISTS state (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        id_user TEXT UNIQUE NOT NULL,
                        tickets_created INTEGER DEFAULT 0,
                        tickets_participated INTEGER DEFAULT 0,
                        comments INTEGER DEFAULT 0,
                        FOREIGN KEY (id_user) REFERENCES USEUR(ID)
                    )
                """)
                if not success:
                    raise Exception("Échec de la création de la table state")
                
                # Table des logs d'activité
                success = self.execute_query("""
                    CREATE TABLE IF NOT EXISTS activity_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT,
                        action TEXT NOT NULL,
                        description TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES USEUR(ID)
                    )
                """)
                if not success:
                    raise Exception("Échec de la création de la table activity_logs")
                
                # Table pour les commentaires de tickets
                self.execute_query("""
                    CREATE TABLE IF NOT EXISTS ticket_comments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ticket_id INTEGER NOT NULL,
                        user_id TEXT NOT NULL,
                        content TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (ticket_id) REFERENCES tiqué(ID_tiqué),
                        FOREIGN KEY (user_id) REFERENCES USEUR(ID)
                    )
                """)
                
            # MySQL version
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
                        ID_tiqué INT AUTO_INCREMENT PRIMARY KEY,
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
                # Supprimer l'ancienne table commentaires MySQL aussi
                self.execute_query("""
                    CREATE TABLE IF NOT EXISTS ticket_comments (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        ticket_id INT NOT NULL,
                        user_id VARCHAR(36) NOT NULL,
                        content TEXT NOT NULL,
                        gravite INT DEFAULT 0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (ticket_id) REFERENCES tiqué(ID_tiqué) ON DELETE CASCADE,
                        FOREIGN KEY (user_id) REFERENCES USEUR(ID)
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
                self.execute_query("""
                    CREATE TABLE IF NOT EXISTS pret (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        id_materiel INT NOT NULL,
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
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        id_materiel INT NOT NULL,
                        id_technicien VARCHAR(36) NOT NULL,
                        type VARCHAR(100) NOT NULL,
                        description TEXT,
                        date_debut DATETIME DEFAULT CURRENT_TIMESTAMP,
                        date_fin DATETIME,
                        statut VARCHAR(50) DEFAULT 'en_cours',
                        FOREIGN KEY (id_materiel) REFERENCES materiel(id) ON DELETE CASCADE
                    )
                """)

        except Exception as e:
            self.logger.error(f"Erreur lors de la création des tables : {str(e)}")
            raise Exception(f"Impossible de créer les tables : {str(e)}")

    def verify_table_structure(self):
        """Vérifie et corrige la structure des tables"""
        try:
            if self.db_type == 'sqlite':
                # Vérifier la table sessions
                sessions_columns = self.execute_query("PRAGMA table_info(sessions)")
                if sessions_columns and isinstance(sessions_columns, list):
                    session_column_names = [col[1] for col in sessions_columns]
                    
                    # Vérifier que les colonnes nécessaires existent
                    required_columns = ['user_id', 'token', 'creation_date', 'expiry_date']
                    missing_columns = []
                    
                    for col in required_columns:
                        if col not in session_column_names:
                            missing_columns.append(col)
                    
                    # Si des colonnes manquent, recréer la table
                    if missing_columns:
                        self.logger.info(f"Colonnes manquantes dans sessions: {missing_columns}")
                        # Sauvegarder les données existantes si possible
                        try:
                            existing_sessions = self.execute_query("SELECT * FROM sessions")
                        except:
                            existing_sessions = []
                        
                        # Supprimer et recréer la table
                        self.execute_query("DROP TABLE IF EXISTS sessions")
                        self.execute_query("""
                            CREATE TABLE sessions (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                user_id TEXT NOT NULL,
                                token TEXT UNIQUE NOT NULL,
                                creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                expiry_date TIMESTAMP NOT NULL,
                                FOREIGN KEY (user_id) REFERENCES USEUR(ID)
                            )
                        """)
                        self.logger.info("Table sessions recréée avec la bonne structure")
                
                # Vérifier la table USEUR
                columns_result = self.execute_query("PRAGMA table_info(USEUR)")
                if columns_result and isinstance(columns_result, list):
                    column_names = [col[1] for col in columns_result]
                    
                    if 'password' not in column_names:
                        self.logger.info("Ajout de la colonne password à la table USEUR")
                        self.execute_query("ALTER TABLE USEUR ADD COLUMN password TEXT")
                    
                    if 'role' not in column_names:
                        self.logger.info("Ajout de la colonne role à la table USEUR")
                        self.execute_query("ALTER TABLE USEUR ADD COLUMN role TEXT DEFAULT 'user'")
                
                # Vérifier la table tiqué
                ticket_result = self.execute_query("PRAGMA table_info(tiqué)")
                if ticket_result and isinstance(ticket_result, list):
                    ticket_column_names = [col[1] for col in ticket_result]
                    
                    # Ajouter ID_technicien si manquant
                    if 'ID_technicien' not in ticket_column_names:
                        self.logger.info("Ajout de la colonne ID_technicien à la table tiqué")
                        success = self.execute_query("ALTER TABLE tiqué ADD COLUMN ID_technicien TEXT")
                        if not success:
                            self.logger.error("Échec de l'ajout de la colonne ID_technicien")
                            return False
                    
                    # Ajouter description si manquant (ou renommer descriptio)
                    if 'description' not in ticket_column_names and 'descriptio' in ticket_column_names:
                        # Renommer descriptio en description
                        self.logger.info("Renommage de la colonne descriptio en description")
                        # SQLite ne supporte pas ALTER COLUMN, on doit recréer la table
                        try:
                            # Créer une nouvelle table avec la bonne structure
                            self.execute_query("""
                                CREATE TABLE tiqué_new (
                                    ID_tiqué INTEGER PRIMARY KEY AUTOINCREMENT,
                                    ID_user TEXT NOT NULL,
                                    titre TEXT NOT NULL,
                                    date_open TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                    date_close TIMESTAMP,
                                    ID_technicien TEXT,
                                    description TEXT,
                                    open INTEGER DEFAULT 1,
                                    tag TEXT,
                                    gravite INTEGER DEFAULT 1,
                                    FOREIGN KEY (ID_user) REFERENCES USEUR(ID),
                                    FOREIGN KEY (ID_technicien) REFERENCES USEUR(ID)
                                )
                            """)
                            
                            # Copier les données
                            self.execute_query("""
                                INSERT INTO tiqué_new (ID_tiqué, ID_user, titre, date_open, date_close, 
                                                     description, open, tag, gravite)
                                SELECT ID_tiqué, ID_user, titre, date_open, date_close, 
                                       descriptio, open, tag, gravite 
                                FROM tiqué
                            """)
                            
                            # Supprimer l'ancienne table et renommer la nouvelle
                            self.execute_query("DROP TABLE tiqué")
                            self.execute_query("ALTER TABLE tiqué_new RENAME TO tiqué")
                            
                            self.logger.info("Table tiqué restructurée avec succès")
                        except Exception as e:
                            self.logger.error(f"Erreur lors de la restructuration de la table tiqué: {str(e)}")
                            return False
                    
                    elif 'description' not in ticket_column_names:
                        # Ajouter la colonne description
                        self.logger.info("Ajout de la colonne description à la table tiqué")
                        success = self.execute_query("ALTER TABLE tiqué ADD COLUMN description TEXT")
                        if not success:
                            self.logger.error("Échec de l'ajout de la colonne description")
                            return False
                    
                    if 'date_close' not in ticket_column_names:
                        self.logger.info("Ajout de la colonne date_close à la table tiqué")
                        success = self.execute_query("ALTER TABLE tiqué ADD COLUMN date_close TIMESTAMP")
                        if not success:
                            self.logger.error("Échec de l'ajout de la colonne date_close")
                            return False
            
            self.logger.info("Structure des tables vérifiée et corrigée")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification de la structure : {str(e)}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    def test_connection(self):
        """
        Teste la connexion à la base de données sans effectuer de modifications.
        Renvoie un tuple (succès, message) où succès est un booléen indiquant si le test est réussi,
        et message est un message explicatif en cas d'échec.
        """
        try:
            if self.db_type == 'sqlite':
                db_path = os.path.join(os.getcwd(), 'glpibis.db')
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

    def get_table_structure(self, table_name):
        """Récupère la structure d'une table"""
        try:
            if self.db_type == 'sqlite':
                return self.execute_query(f"PRAGMA table_info({table_name})")
            elif self.db_type == 'mysql':
                return self.execute_query(f"DESCRIBE {table_name}")
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération de la structure de la table {table_name}: {str(e)}")
            return None

    def get_table_data(self, table_name, page=1, per_page=50, filters=None, sort_by=None):
        """Récupère les données d'une table avec pagination et filtres"""
        try:
            query = f"SELECT * FROM {table_name}"
            params = []
            
            if filters:
                where_clauses = []
                for key, value in filters.items():
                    where_clauses.append(f"{key} = ?")
                    params.append(value)
                if where_clauses:
                    query += " WHERE " + " AND ".join(where_clauses)
            
            if sort_by:
                query += f" ORDER BY {sort_by}"
                
            query += " LIMIT ? OFFSET ?"
            params.extend([per_page, (page - 1) * per_page])
            
            return self.execute_query(query, params)
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des données de {table_name}: {str(e)}")
            return None

    def get_table_count(self, table_name, filters=None):
        """Compte le nombre total d'enregistrements dans une table"""
        try:
            query = f"SELECT COUNT(*) FROM {table_name}"
            params = []
            
            if filters:
                where_clauses = []
                for key, value in filters.items():
                    where_clauses.append(f"{key} = ?")
                    params.append(value)
                if where_clauses:
                    query += " WHERE " + " AND ".join(where_clauses)
            
            result = self.execute_query(query, params)
            return result[0][0] if result else 0
            
        except Exception as e:
            self.logger.error(f"Erreur lors du comptage des enregistrements de {table_name}: {str(e)}")
            return 0

    def update_table_row(self, table_name, row_id, data):
        """Met à jour une ligne dans une table"""
        try:
            set_clauses = []
            params = []
            
            for key, value in data.items():
                set_clauses.append(f"{key} = ?")
                params.append(value)
            
            query = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE id = ?"
            params.append(row_id)
            
            return self.execute_query(query, params)
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la mise à jour de la ligne {row_id} dans {table_name}: {str(e)}")
            return False

    def delete_table_row(self, table_name, row_id):
        """Supprime une ligne d'une table"""
        try:
            query = f"DELETE FROM {table_name} WHERE id = ?"
            return self.execute_query(query, [row_id])
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la suppression de la ligne {row_id} dans {table_name}: {str(e)}")
            return False
            
    def add_table_row(self, table_name, data):
        """Ajoute une nouvelle ligne dans une table"""
        try:
            columns = ", ".join(data.keys())
            placeholders = ", ".join(["?" for _ in data])
            query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
            
            return self.execute_query(query, list(data.values()))
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'ajout d'une ligne dans {table_name}: {str(e)}")
            return False
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
    """
    if query == 'connect':
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

def fix_database_structure():
    """Corrige la structure de la base de données au démarrage"""
    try:
        from utils.logger import app_logger
        app_logger.info("Vérification et correction de la structure de la base de données...")
        
        # Créer les tables manquantes
        create_missing_tables()
        
        # Vérifier et corriger la table tiqué
        columns = get_db("PRAGMA table_info(tiqué)")
        column_names = [col[1] for col in columns] if columns else []
        
        changes_made = False
        
        # Corriger la colonne description/descriptio
        if 'description' not in column_names and 'descriptio' in column_names:
            app_logger.info("Correction de la colonne 'descriptio' -> 'description'")
            
            # Créer une nouvelle table avec la bonne structure
            get_db("""
                CREATE TABLE tiqué_temp (
                    ID_tiqué INTEGER PRIMARY KEY AUTOINCREMENT,
                    ID_user TEXT NOT NULL,
                    titre TEXT NOT NULL,
                    date_open TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    date_close TIMESTAMP,
                    ID_technicien TEXT,
                    description TEXT,
                    open INTEGER DEFAULT 1,
                    tag TEXT,
                    gravite INTEGER DEFAULT 1,
                    FOREIGN KEY (ID_user) REFERENCES USEUR(ID),
                    FOREIGN KEY (ID_technicien) REFERENCES USEUR(ID)
                )
            """)
            
            # Copier les données
            get_db("""
                INSERT INTO tiqué_temp (ID_tiqué, ID_user, titre, date_open, date_close, 
                                      ID_technicien, description, open, tag, gravite)
                SELECT ID_tiqué, ID_user, titre, date_open, date_close, 
                       ID_technicien, descriptio, open, tag, gravite 
                FROM tiqué
            """)
            
            # Remplacer l'ancienne table
            get_db("DROP TABLE tiqué")
            get_db("ALTER TABLE tiqué_temp RENAME TO tiqué")
            changes_made = True
            
        # Ajouter les colonnes manquantes
        missing_columns = {
            'ID_technicien': 'TEXT',
            'date_close': 'TIMESTAMP',
            'description': 'TEXT'
        }
        
        for column, column_type in missing_columns.items():
            if column not in column_names:
                try:
                    get_db(f"ALTER TABLE tiqué ADD COLUMN {column} {column_type}")
                    app_logger.info(f"Colonne '{column}' ajoutée à la table tiqué")
                    changes_made = True
                except Exception as col_error:
                    app_logger.warning(f"Impossible d'ajouter la colonne {column}: {str(col_error)}")
        
        if changes_made:
            app_logger.info("Structure de la base de données corrigée avec succès")
        else:
            app_logger.info("Structure de la base de données déjà correcte")
            
    except Exception as e:
        from utils.logger import app_logger
        app_logger.error(f"Erreur lors de la correction de la structure: {str(e)}")

def create_missing_tables():
    """Crée les tables manquantes si elles n'existent pas"""
    try:
        # Table des commentaires de tickets
        get_db("""
            CREATE TABLE IF NOT EXISTS ticket_comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER NOT NULL,
                user_id TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ticket_id) REFERENCES tiqué(ID_tiqué),
                FOREIGN KEY (user_id) REFERENCES USEUR(ID)
            )
        """)
        
        # Table d'inventaire
        get_db("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                location TEXT,
                status TEXT DEFAULT 'active',
                serial_number TEXT,
                purchase_date DATE,
                warranty_end DATE,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table des logs d'activité
        get_db("""
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                description TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES USEUR(ID)
            )
        """)
        
    except Exception as e:
        from utils.logger import app_logger
        app_logger.error(f"Erreur lors de la création des tables manquantes: {str(e)}")
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

# Listage des tables de la base de données
def get_tables_list():
    """
    Retourne la liste des tables dans la base de données.
    """
    try:
        if db_manager is None:
            raise RuntimeError("db_manager n'est pas initialisé. Veuillez initialiser la base de données avant d'appeler cette fonction.")
        if db_manager.db_type == 'sqlite':
            return db_manager.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
        elif db_manager.db_type == 'mysql':
            return db_manager.execute_query("SHOW TABLES")
        else:
            raise ValueError(f"Type de base de données non supporté: {db_manager.db_type}")
    except Exception as e:
        from utils.logger import app_logger
        app_logger.error(f"Erreur lors de la récupération des tables: {str(e)}")
        return []