import pytest
import sys
import os
import uuid

# Ajouter le dossier racine au chemin de recherche des modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from app import app
from utils.db_manager import get_db
from onekey.auth import register_user, login_user

@pytest.fixture
def client():
    """Fixture pour créer un client de test"""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    client = app.test_client()
    
    yield client

def test_login_sql_injection():
    """Test de sécurité contre les injections SQL lors de la connexion"""
    # Test avec une tentative d'injection SQL dans le champ email
    injection_email = "' OR 1=1; --"
    result = login_user(injection_email, "anypassword")
    
    # S'assurer que l'injection ne fonctionne pas
    assert result.get('status') == 'error'
    
    # Test avec une tentative d'injection SQL dans le champ mot de passe
    test_id = str(uuid.uuid4())
    test_email = f"secure_test_{test_id}@example.com"
    test_password = "SecurePassword123!"
    
    # Créer un utilisateur de test légitime
    try:
        user_id = register_user("Secure Test", "30", "1234567890", test_email, test_password)
        
        # Tentative d'injection dans le mot de passe
        injection_password = "' OR 1=1; --"
        result = login_user(test_email, injection_password)
        
        # S'assurer que l'injection ne fonctionne pas
        assert result.get('status') == 'error'
    except Exception as e:
        pytest.fail(f"Erreur lors du test d'injection SQL: {e}")
    finally:
        # Nettoyer après le test
        if 'user_id' in locals() and user_id:
            get_db("DELETE FROM USEUR WHERE ID = %s", (user_id,))

def test_search_sql_injection(client):
    """Test de sécurité contre les injections SQL lors des recherches"""
    # Tentative d'injection dans un paramètre de recherche
    response = client.get('/tickets/search?query=' + "' OR 1=1; --")
    
    # Vérifier que la réponse est correcte et ne révèle pas de données sensibles
    assert response.status_code in [200, 302, 404]  # La réponse peut varier selon l'implémentation
    
    # Vérifier l'absence d'erreurs SQL dans la réponse
    assert b"MySQL" not in response.data
    assert b"SQL syntax" not in response.data
    assert b"SQL error" not in response.data

def test_inventory_search_sql_injection(client):
    """Test de sécurité contre les injections SQL dans la recherche d'inventaire"""
    # Tentative d'injection dans un paramètre de recherche d'inventaire
    response = client.get('/inventory/search?query=' + "'; DROP TABLE materiel; --")
    
    # Vérifier que la réponse est correcte
    assert response.status_code in [200, 302, 404]  # La réponse peut varier selon l'implémentation
    
    # Vérifier l'absence d'erreurs SQL dans la réponse
    assert b"MySQL" not in response.data
    assert b"SQL syntax" not in response.data
    assert b"SQL error" not in response.data
    
    # Vérifier que la table existe toujours (l'injection n'a pas fonctionné)
    result = get_db("SHOW TABLES LIKE 'materiel'")
    assert result is not None and len(result) > 0

def test_user_creation_sql_injection():
    """Test de sécurité contre les injections SQL lors de la création d'utilisateur"""
    # Tentative d'injection dans le nom d'utilisateur
    injection_name = "Test'; INSERT INTO USEUR VALUES ('hack', 'hacker', 'hack@example.com', 'hacked', 'admin'); --"
    test_id = str(uuid.uuid4())
    test_email = f"injection_test_{test_id}@example.com"
    test_password = "Password123!"
    
    try:
        # Tenter de créer un utilisateur avec une injection SQL
        user_id = register_user(injection_name, "30", "1234567890", test_email, test_password)
        
        # Vérifier que l'utilisateur a été créé normalement
        user = get_db("SELECT * FROM USEUR WHERE ID = %s", (user_id,))
        assert user is not None and len(user) > 0
        
        # Trouver l'index qui contient le nom
        user_data = user[0]
        name_found = False
        
        # Comme nous ne sommes pas sûrs de l'indice exact du nom, vérifions le contenu
        # En particulier, vérifions que l'injection SQL a été traitée comme une simple chaîne
        for value in user_data:
            if value == injection_name:
                name_found = True
                break
        
        assert name_found, "Le nom avec injection SQL n'a pas été correctement stocké en tant que texte"
        
        # Vérifier qu'aucun utilisateur "hacker" n'a été créé par l'injection
        hacker = get_db("SELECT * FROM USEUR WHERE email = ?", ("hack@example.com",))
        assert not hacker or len(hacker) == 0
    except Exception as e:
        pytest.fail(f"Erreur lors du test d'injection SQL: {e}")
    finally:
        # Nettoyer après le test
        if 'user_id' in locals() and user_id:
            get_db("DELETE FROM USEUR WHERE ID = %s", (user_id,))


