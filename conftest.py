# conftest.py

import os
import sqlite3
import pytest

@pytest.fixture(scope="session")
def db():
    db_file = os.path.join(os.path.dirname(__file__), "database.db")
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS USEUR (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_created DATE NOT NULL,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            phone_number TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        )
    """)
    # Loop to find and delete users with emails ending in '@example.com'
    while True:
        cursor.execute("SELECT email FROM USEUR WHERE email LIKE ?", ('%@example.com',))
        result = cursor.fetchone()
        if result:
            email_to_delete = result[0]
            cursor.execute("DELETE FROM USEUR WHERE email = ?", (email_to_delete,))
            conn.commit()
        else:
            break
    yield db_file
    conn.close()