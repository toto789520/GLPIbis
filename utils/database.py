import sqlite3
import mysql.connector
from mysql.connector import Error
from utils.logger import get_logger

class DBManager:
    def __init__(self, db_type, db_config):
        self.db_type = db_type
        self.db_config = db_config
        self.connection = None
        self.logger = get_logger()
        self.connect()

    def connect(self):
        """Établit la connexion à la base de données"""
        try:
            if self.db_type == "sqlite":
                self.connection = sqlite3.connect(self.db_config['database'])
                self.logger.info(f"Connexion à la base de données SQLite réussie: {self.db_config['database']}")
            elif self.db_type == "mysql":
                self.connection = mysql.connector.connect(
                    host=self.db_config['host'],
                    user=self.db_config['user'],
                    password=self.db_config['password'],
                    database=self.db_config['database']
                )
                self.logger.info(f"Connexion à la base de données MySQL réussie: {self.db_config['database']}")
            else:
                self.logger.error(f"Type de base de données non supporté: {self.db_type}")
        except Error as e:
            self.logger.error(f"Erreur lors de la connexion à la base de données: {e}")
            raise e

    def cursor(self):
        """Retourne un curseur pour la base de données"""
        if self.db_type == "sqlite":
            return self.connection.cursor()
        elif self.db_type == "mysql":
            return self.connection.cursor()
        else:
            raise ValueError(f"Type de base de données non supporté: {self.db_type}")
    
    def get_tickets_stats(self):
        """Récupère les statistiques des tickets"""
        try:
            cursor = self.cursor()
            cursor.execute("SELECT COUNT(*) FROM tiqué WHERE open = 1")
            open_tickets = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM tiqué WHERE open = 0")
            closed_tickets = cursor.fetchone()[0]
            
            cursor.close()
            return {
                'open': open_tickets,
                'closed': closed_tickets,
                'total': open_tickets + closed_tickets
            }
        except Exception as e:
            self.logger.debug(f"Impossible de récupérer les statistiques des tickets: {e}")
            return {'open': 0, 'closed': 0, 'total': 0}
    
    def get_users_count(self):
        """Récupère le nombre d'utilisateurs"""
        try:
            cursor = self.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            count = cursor.fetchone()[0]
            cursor.close()
            return count
        except Exception as e:
            self.logger.debug(f"Impossible de récupérer le nombre d'utilisateurs: {e}")
            return 0
    
    def get_inventory_count(self):
        """Récupère le nombre d'éléments d'inventaire"""
        try:
            cursor = self.cursor()
            cursor.execute("SELECT COUNT(*) FROM inventory")
            count = cursor.fetchone()[0]
            cursor.close()
            return count
        except Exception as e:
            self.logger.debug(f"Impossible de récupérer le nombre de matériels: {e}")
            return 0

    def close(self):
        """Ferme la connexion à la base de données"""
        if self.connection:
            self.connection.close()
            self.logger.info("Connexion à la base de données fermée")