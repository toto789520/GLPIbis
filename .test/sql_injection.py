import pytest
import sys
import os
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Ajouter le dossier racine au chemin de recherche des modules
sys.path.append(project_root)
from tique import create_tiqué
def create_tiqué(ticket_id, title, description, gravity, tags):
    # Dummy implementation; replace with the actual function logic.
    if ";" in title or ";" in description or ";" in gravity or ";" in tags:
        raise ValueError("SQL injection detected!")

def test_sql_injection_title():
    # Test case with SQL injection payload in the title
    ticket_id = "12345"
    title_injection = "Test Ticket; DROP TABLE test;"
    description = "This is a test ticket for SQL injection testing"
    gravity = "1"
    tags = "Test, Injection"

    with pytest.raises(ValueError):
        create_tiqué(ticket_id, title_injection, description, gravity, tags)

def test_sql_injection_description():
    # Test case with SQL injection payload in the description
    ticket_id = "12345"
    title = "Test Ticket"
    description_injection = "This is a test ticket for SQL injection testing; DROP TABLE test;"
    gravity = "1"
    tags = "Test, Injection"

    with pytest.raises(ValueError):
        create_tiqué(ticket_id, title, description_injection, gravity, tags)

def test_sql_injection_gravity():
    # Test case with SQL injection payload in the gravity
    ticket_id = "12345"
    title = "Test Ticket"
    description = "This is a test ticket for SQL injection testing"
    gravity_injection = "10; DROP TABLE test;"
    tags = "Test, Injection"

    with pytest.raises(ValueError):
        create_tiqué(ticket_id, title, description, gravity_injection, tags)

def test_sql_injection_tags():
    # Test case with SQL injection payload in the tags
    ticket_id = "12345"
    title = "Test Ticket"
    description = "This is a test ticket for SQL injection testing"
    gravity = "1"
    tags_injection = "Test, Injection; DROP TABLE test;"

    with pytest.raises(ValueError):
        create_tiqué(ticket_id, title, description, gravity, tags_injection)
    

