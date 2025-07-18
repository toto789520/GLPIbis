"""
Configuration pytest générée automatiquement par pyclean
"""

import pytest

@pytest.fixture
def app():
    """Fixture pour l'application (à adapter selon votre projet)."""
    # TODO: Retourner votre instance d'application
    pass

@pytest.fixture
def client(app):
    """Fixture pour le client de test (à adapter selon votre projet)."""
    # TODO: Retourner votre client de test
    pass

# Fixtures détectées dans le projet:
# - client (test\test_activity.py)
# - setup_test_activity (test\test_activity.py)
# - setup_test_db (test\test_auth.py)
# - client (test\test_inventory.py)
# - setup_test_categories (test\test_inventory.py)
# - setup_test_item (test\test_inventory.py)
# - client (test\test_sql_injection.py)
# - client (test\test_tickets.py)
# - setup_test_user (test\test_tickets.py)
# - setup_test_ticket (test\test_tickets.py)
