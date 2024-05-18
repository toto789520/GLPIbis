import pytest
import sqlite3
from tique import create_tiqué, close_tiqué

def test_create_tiqué():
    # Create a tiqué with sample data
    ID_user = 123456
    titre = "Sample Tiqué"
    description = "This is a sample tiqué."
    gravité = 1
    tags = "tag1, tag2"
    tiqué_id = create_tiqué(ID_user, titre, description, gravité, tags)

    # Check if the tiqué was created successfully
    assert tiqué_id is not None
    conn = sqlite3.connect('database.db')  # Updated connection string
    cursor = conn.cursor()
    cursor.execute("DELETE * FROM tiqué WHERE ID_tiqué=?", (tiqué_id,))

def test_close_tiqué():
    # Create a tiqué for testing
    tiqué_id = create_tiqué(123456, "Sample Tiqué", "This is a sample tiqué.", 1, "tag1, tag2")

    # Close the tiqué
    result = close_tiqué(tiqué_id)

    # Check if the tiqué was closed successfully
    assert result is True