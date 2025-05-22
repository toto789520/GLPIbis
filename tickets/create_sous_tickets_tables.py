import sqlite3
from utils.db_manager import get_db

def create_sous_tickets_tables():
    """
    Create the sous_tickets related tables and add the nombre_sous_tickets column to tiqué if missing.
    """
    try:
        conn = get_db('connect')
        cursor = conn.cursor()

        # Create sous_tickets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sous_tickets (
                id TEXT PRIMARY KEY,
                parent_ticket_id INTEGER NOT NULL,
                titre TEXT NOT NULL,
                description TEXT,
                statut TEXT DEFAULT 'ouvert',
                priorite INTEGER DEFAULT 5,
                createur_id TEXT NOT NULL,
                assigne_a TEXT,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                date_modification TIMESTAMP,
                date_resolution TIMESTAMP,
                FOREIGN KEY (parent_ticket_id) REFERENCES tiqué(ID_tiqué),
                FOREIGN KEY (createur_id) REFERENCES USEUR(ID),
                FOREIGN KEY (assigne_a) REFERENCES USEUR(ID)
            )
        """)

        # Create sous_tickets_historique table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sous_tickets_historique (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sous_ticket_id TEXT NOT NULL,
                action TEXT NOT NULL,
                user_id TEXT,
                date_action TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sous_ticket_id) REFERENCES sous_tickets(id),
                FOREIGN KEY (user_id) REFERENCES USEUR(ID)
            )
        """)

        # Create sous_tickets_commentaires table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sous_tickets_commentaires (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sous_ticket_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                commentaire TEXT,
                date_commentaire TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sous_ticket_id) REFERENCES sous_tickets(id),
                FOREIGN KEY (user_id) REFERENCES USEUR(ID)
            )
        """)

        # Create sous_tickets_dependances table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sous_tickets_dependances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sous_ticket_id TEXT NOT NULL,
                dependance_id TEXT NOT NULL,
                FOREIGN KEY (sous_ticket_id) REFERENCES sous_tickets(id),
                FOREIGN KEY (dependance_id) REFERENCES sous_tickets(id)
            )
        """)

        # Add nombre_sous_tickets column to tiqué if not exists
        cursor.execute("PRAGMA table_info(tiqué)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'nombre_sous_tickets' not in columns:
            cursor.execute("ALTER TABLE tiqué ADD COLUMN nombre_sous_tickets INTEGER DEFAULT 0")

        conn.commit()
        cursor.close()
        return True
    except Exception as e:
        print(f"Error creating sous_tickets tables: {e}")
        return False
