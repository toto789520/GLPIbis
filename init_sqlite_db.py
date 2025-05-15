import sqlite3
import os

import os
import sqlite3

import os
import sqlite3

def initialize_sqlite_db():
    """Initialise la base de données SQLite avec toutes les tables nécessaires."""
    db_path = os.path.join(os.getcwd(), 'database.sqlite')
    
    # Ne pas supprimer la base de données si elle existe déjà
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Table USEUR avec toutes les colonnes nécessaires
    cursor.execute("""
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
    );
    """)

    # Table tickets (tiqué)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tiqué (
        ID_tiqué INTEGER PRIMARY KEY AUTOINCREMENT,
        titre TEXT NOT NULL,
        description TEXT,
        gravite INTEGER DEFAULT 5,
        open INTEGER DEFAULT 1,
        tag TEXT DEFAULT 'en_attente',
        ID_user INTEGER,
        date_open TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (ID_user) REFERENCES USEUR(ID)
    );
    """)

    # Table activity_logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS activity_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        action_type TEXT NOT NULL,
        module TEXT NOT NULL,
        description TEXT,
        timestamp DATETIME NOT NULL
    );
    """)

    # Table inventory
    cursor.execute("""
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
    );
    """)

    # Créer les index
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_email ON USEUR(email);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_ticket_status ON tiqué(open, tag);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_activity_user ON activity_logs(user_id);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_activity_timestamp ON activity_logs(timestamp);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_inventory_status ON inventory(status);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_inventory_serial ON inventory(serial_number);')

    conn.commit()
    conn.close()
    print(f"Base de données SQLite initialisée avec succès à {db_path}")

if __name__ == "__main__":
    try:
        initialize_sqlite_db()
    except Exception as e:
        print(f"Erreur lors de l'initialisation de la base de données : {e}")
