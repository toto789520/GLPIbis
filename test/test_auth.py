import pytest
import sys
import os
import uuid
from datetime import datetime

# Ajouter le dossier racine au chemin de recherche des modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from onekey.auth import register_user, login_user
from utils.db_manager import get_db

@pytest.fixture(scope="session", autouse=True)
def init_test_db():
    """Fixture pour initialiser la connexion à la base de données de test"""
    from utils.db_manager import init_db_manager  # Assurez-vous que ces fonctions existent dans db_manager/__init__.py
    init_db_manager()
    yield
    # close_connection()  # Commented out or remove if not defined

@pytest.fixture
def setup_test_db(init_test_db):
    """Fixture pour configurer la base de données de test"""
    # Générer un ID unique pour les tests
    test_id = str(uuid.uuid4())
    test_email = f"test_{test_id}@example.com"
    test_password = "Password123!"
    
    # Créer un utilisateur de test
    try:
        user_id = register_user("Test User", "25", "1234567890", test_email, test_password)
    except Exception as e:
        print(f"Erreur lors de la création de l'utilisateur de test: {e}")
        user_id = None
    
    yield {
        "email": test_email,
        "password": test_password,
        "user_id": user_id
    }
    
    # Nettoyage après les tests
    if user_id:
        get_db("DELETE FROM USEUR WHERE ID = %s", (user_id,))

def test_user_registration(init_test_db):
    """Test de la création d'un utilisateur"""
    test_id = str(uuid.uuid4())
    test_email = f"test_creation_{test_id}@example.com"
    test_password = "SecurePassword123!"
    
    try:
        user_id = register_user("Test Creation", 30, "0987654321", test_email, test_password)
        assert user_id is not None

        user = get_db("SELECT * FROM USEUR WHERE ID = ?", (user_id,))
        assert user is not None and len(user) > 0
        user_row = user[0]
        assert test_email in user_row  # Vérifie que l'email est présent dans les données
        assert "Test Creation" in user_row  # Vérifie que le nom est présent dans les données

    finally:
        if 'user_id' in locals() and user_id:
            get_db("DELETE FROM USEUR WHERE ID = ?", (user_id,))

def test_login_success(setup_test_db):
    """Test d'un login réussi"""
    test_data = setup_test_db
    if not test_data["user_id"]:
        pytest.skip("Configuration de test échouée, impossible de créer l'utilisateur test")
    
    # Tenter de se connecter
    result = login_user(test_data["email"], test_data["password"])
    
    # Vérifier que la connexion a réussi
    assert result is not None
    assert result.get('status') == 'success'
    assert result.get('email') == test_data["email"]

def test_login_wrong_password(setup_test_db):
    """Test d'un login avec un mot de passe incorrect"""
    test_data = setup_test_db
    if not test_data["user_id"]:
        pytest.skip("Configuration de test échouée, impossible de créer l'utilisateur test")
    
    # Tenter de se connecter avec un mauvais mot de passe
    result = login_user(test_data["email"], "WrongPassword123!")
    
    # Vérifier que la connexion a échoué
    assert result.get('status') == 'error'

def test_login_nonexistent_user(init_test_db):
    """Test de connexion avec un utilisateur qui n'existe pas"""
    result = login_user("nonexistent@example.com", "Password123!")
    assert result.get('status') == 'error'
    assert result.get('user_id') is None