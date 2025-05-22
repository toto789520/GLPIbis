from utils.db_manager import get_db

def initialize_mysql():
    """Initialise la base de données MySQL avec les tables nécessaires."""
    get_db("""
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        role ENUM('admin', 'user') DEFAULT 'user',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS tickets (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        description TEXT,
        status ENUM('open', 'closed', 'pending') DEFAULT 'open',
        priority INT DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    );
    """)

if __name__ == "__main__":
    try:
        initialize_mysql()
        print("Base de données MySQL initialisée avec succès.")
    except Exception as e:
        print(f"Erreur lors de l'initialisation de MySQL : {e}")