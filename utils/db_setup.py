from utils.db import get_db

def create_tables():
    """Create necessary tables for EcoleDirecte integration."""
    # Create schedules table
    get_db("""
        CREATE TABLE IF NOT EXISTS schedules (
            id INT AUTO_INCREMENT PRIMARY KEY,
            class_name VARCHAR(255) NOT NULL,
            subject VARCHAR(255) NOT NULL,
            start_time DATETIME NOT NULL,
            end_time DATETIME NOT NULL,
            room VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create rooms table
    get_db("""
        CREATE TABLE IF NOT EXISTS rooms (
            id INT AUTO_INCREMENT PRIMARY KEY,
            room_name VARCHAR(255) NOT NULL,
            capacity INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

if __name__ == "__main__":
    create_tables()
