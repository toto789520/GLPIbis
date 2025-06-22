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

@pytest.fixture
def setup_test_db():
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

def test_user_registration():
    """Test de la création d'un utilisateur"""
    test_id = str(uuid.uuid4())
    test_email = f"test_creation_{test_id}@example.com"
    test_password = "SecurePassword123!"
    
    # Créer un utilisateur
    try:
        user_id = register_user("Test Creation", "30", "0987654321", test_email, test_password)
        
        # Vérifier que l'utilisateur a été créé avec succès
        assert user_id is not None
        
        # Récupérer l'utilisateur créé
        user = get_db("SELECT * FROM USEUR WHERE ID = %s", (user_id,))
        
        # Vérifier que les informations sont correctes
        assert user is not None
        assert len(user) > 0
        
        # Nous devons déterminer quel index contient le nom et l'email
        # D'après l'erreur, il semble que l'index 1 contient une date, pas le nom
        # Affichons le contenu pour le debugging
        user_data = user[0]
        
        # Trouver l'index qui contient le nom et l'email
        name_index = None
        email_index = None
        
        for i, value in enumerate(user_data):
            if value == "Test Creation":
                name_index = i
            if value == test_email:
                email_index = i
        
        # Vérifier que nous avons pu trouver le nom et l'email
        assert name_index is not None, "Impossible de trouver le nom dans les données utilisateur"
        assert email_index is not None, "Impossible de trouver l'email dans les données utilisateur"
        
        # Vérifier que les valeurs sont correctes
        assert user_data[name_index] == "Test Creation"
        assert user_data[email_index] == test_email
        
    except Exception as e:
        pytest.fail(f"L'enregistrement de l'utilisateur a échoué: {e}")
    finally:
        # Nettoyer après le test
        if 'user_id' in locals() and user_id:
            get_db("DELETE FROM USEUR WHERE ID = %s", (user_id,))

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

def test_login_nonexistent_user():
    """Test de connexion avec un utilisateur qui n'existe pas"""
    from onekey.auth import login_user
    
    # Tenter de se connecter avec un email qui n'existe pas
    result = login_user("utilisateur_inexistant@example.com", "motdepasse123")
    
    # Vérifier que la connexion a échoué
    assert result['status'] == 'error'
    assert 'utilisateur' in result['message'].lower() or 'existe' in result['message'].lower()
    assert result['user_id'] is None