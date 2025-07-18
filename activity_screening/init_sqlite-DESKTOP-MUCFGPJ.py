import sqlite3
import os

def initialize_sqlite():
    """Initialise la base de données SQLite avec les tables nécessaires."""
    db_path = os.path.join(os.getcwd(), 'database.sqlite')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Création de la table USEUR (au lieu de users)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS USEUR (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        hashed_password TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        dete_de_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Création de la table tickets
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        status TEXT DEFAULT 'open',
        priority INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    conn.close()
    print(f"Base de données SQLite initialisée à {db_path}.")

if __name__ == "__main__":
    try:
        initialize_sqlite()
    except Exception as e:
        print(f"Erreur lors de l'initialisation de SQLite : {e}")