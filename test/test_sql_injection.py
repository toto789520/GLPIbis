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
from inventory.inventory_service import inventory_service
from utils.logger import app_logger

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
    """Test de sécurité contre l'injection SQL dans la recherche d'inventaire"""
    
    # Tests d'injection SQL courantes
    malicious_inputs = [
        "'; DROP TABLE inventory; --",
        "' OR '1'='1",
        "' UNION SELECT * FROM USEUR --",
        "'; DELETE FROM inventory; --",
        "' OR 1=1 --",
        "admin'--",
        "' OR 'x'='x",
        "'; INSERT INTO inventory (name) VALUES ('hacked'); --",
        "' AND (SELECT COUNT(*) FROM USEUR) > 0 --",
        "' OR SLEEP(5) --"
    ]
    
    for malicious_input in malicious_inputs:
        try:
            app_logger.info(f"Test d'injection SQL avec l'entrée: {malicious_input}")
            
            # Test de la recherche avec une entrée malveillante
            results = inventory_service.get_all_items(search_term=malicious_input)
            
            # Vérifier que la fonction retourne un résultat sûr
            assert isinstance(results, list), f"La fonction doit retourner une liste, même avec une entrée malveillante: {malicious_input}"
            
            # Vérifier que les résultats ne contiennent pas de données sensibles inattendues
            for result in results:
                assert isinstance(result, dict), "Chaque résultat doit être un dictionnaire"
                assert 'id' in result, "Chaque résultat doit avoir un ID"
                assert 'name' in result, "Chaque résultat doit avoir un nom"
            
            app_logger.info(f"✓ Test d'injection SQL réussi pour: {malicious_input}")
            
        except Exception as e:
            # En cas d'erreur, vérifier que ce n'est pas une injection réussie
            error_msg = str(e).lower()
            
            # Ces mots-clés indiquent une possible injection réussie
            dangerous_keywords = ['syntax error', 'sql error', 'database', 'table', 'column']
            
            if any(keyword in error_msg for keyword in dangerous_keywords):
                pytest.fail(f"Possible injection SQL détectée avec l'entrée '{malicious_input}': {str(e)}")
            
            # Sinon, c'est probablement une erreur normale de validation
            app_logger.info(f"✓ Entrée malveillante correctement rejetée: {malicious_input}")

def test_inventory_category_filter_sql_injection():
    """Test d'injection SQL sur le filtre de catégorie"""
    
    malicious_categories = [
        "'; DROP TABLE inventory; --",
        "' OR '1'='1",
        "' UNION SELECT password FROM USEUR --"
    ]
    
    for malicious_category in malicious_categories:
        try:
            results = inventory_service.get_all_items(category_filter=malicious_category)
            
            # Doit retourner une liste vide ou des résultats valides, pas d'erreur SQL
            assert isinstance(results, list)
            
            app_logger.info(f"✓ Test d'injection SQL sur catégorie réussi pour: {malicious_category}")
            
        except Exception as e:
            error_msg = str(e).lower()
            dangerous_keywords = ['syntax error', 'sql error', 'database', 'table']
            
            if any(keyword in error_msg for keyword in dangerous_keywords):
                pytest.fail(f"Injection SQL possible sur le filtre de catégorie: {malicious_category}")

def test_inventory_status_filter_sql_injection():
    """Test d'injection SQL sur le filtre de statut"""
    
    malicious_statuses = [
        "'; UPDATE inventory SET name='hacked'; --",
        "' OR 1=1 --",
        "' UNION SELECT email, password FROM USEUR --"
    ]
    
    for malicious_status in malicious_statuses:
        try:
            results = inventory_service.get_all_items(status_filter=malicious_status)
            
            assert isinstance(results, list)
            
            app_logger.info(f"✓ Test d'injection SQL sur statut réussi pour: {malicious_status}")
            
        except Exception as e:
            error_msg = str(e).lower()
            if 'sql' in error_msg or 'database' in error_msg:
                pytest.fail(f"Injection SQL possible sur le filtre de statut: {malicious_status}")

def test_inventory_create_sql_injection():
    """Test d'injection SQL lors de la création d'éléments"""
    
    malicious_data = {
        'name': "'; DROP TABLE USEUR; --",
        'category': "' OR '1'='1",
        'description': "'; DELETE FROM sessions; --",
        'serial_number': "' UNION SELECT password FROM USEUR --"
    }
    
    try:
        # Tenter de créer un élément avec des données malveillantes
        result = inventory_service.create_item(malicious_data)
        
        # Si la création réussit, vérifier que les données sont bien échappées
        if result:
            created_item = inventory_service.get_item_by_id(result)
            if created_item:
                # Les données malveillantes doivent être stockées comme du texte normal
                assert created_item['name'] == malicious_data['name']
                assert created_item['category'] == malicious_data['category']
                
                # Nettoyer après le test
                inventory_service.delete_item(result)
        
        app_logger.info("✓ Test d'injection SQL sur création d'élément réussi")
        
    except Exception as e:
        error_msg = str(e).lower()
        if 'sql' in error_msg or 'syntax' in error_msg:
            pytest.fail(f"Injection SQL possible lors de la création: {str(e)}")

if __name__ == "__main__":
    # Exécuter les tests si le fichier est lancé directement
    test_inventory_search_sql_injection(None)
    test_inventory_category_filter_sql_injection()
    test_inventory_status_filter_sql_injection()
    test_inventory_create_sql_injection()
    print("✅ Tous les tests de sécurité SQL ont réussi !")


