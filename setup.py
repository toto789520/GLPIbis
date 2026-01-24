from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()  # Charge .env en premier

DB_URI = os.getenv('db_url')  # Récupérer l'URI de la base de données depuis une variable d'environnement

# Contrôle du logging SQL via une variable d'environnement (désactivé par défaut)
SQL_ECHO = os.getenv('SQLALCHEMY_ECHO', 'false').lower() in ('1', 'true', 'yes', 'y', 'on', 'debug')

# Création de l'engine (pymysql gère bien les URIs mysql://)
engine = create_engine(DB_URI, echo=SQL_ECHO)  # Utiliser SQL_ECHO pour activer/désactiver les logs SQL

try:
    with engine.connect() as connection:
        # Test de connexion : requête simple
        result = connection.execute(text("SELECT VERSION()"))
        version = result.fetchone()[0]
        print(f"Connexion réussie ! Version MySQL : {version}")
        
        # Exemple : lister les tables
        result = connection.execute(text("SHOW TABLES"))
        tables = result.fetchall()
        print("Tables :", [row[0] for row in tables])

        # Création de la table ticket

        
except Exception as e:
    print(f"Erreur de connexion : {e}")
finally:
    engine.dispose()
