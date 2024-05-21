import pytest
import sqlite3
from tique import create_tiqué, close_tiqué, now_comment
def ardclose(ID_tiqué):
    conn = sqlite3.connect('database.db')  # Updated connection string
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tiqué WHERE ID_tiqué=?", (ID_tiqué,))
    conn.commit()
    conn.close()
    conn = sqlite3.connect('comm.db')  # Updated connection string
    cursor = conn.cursor()
    cursor.execute(f"drop table {ID_tiqué}")
    conn.commit()
    conn.close()
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
    ardclose(tiqué_id)



def test_close_tiqué():
    # Create a tiqué with sample data
    ID_user = 123456
    titre = "Sample Tiqué"
    description = "This is a sample tiqué."
    gravité = 1
    tags = "tag1, tag2"
    tiqué_id = create_tiqué(ID_user, titre, description, gravité, tags)
    now_comment(tiqué_id, ID_user, "test tiqué")
    # Close the tiqué
    result = close_tiqué(tiqué_id)
    ardclose(tiqué_id)
    # Check if the tiqué was closed successfully
    assert result is True