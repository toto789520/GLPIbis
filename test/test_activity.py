import pytest
import sys
import os
import uuid
from datetime import datetime, timedelta

# Ajouter le dossier racine au chemin de recherche des modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from app import app
from utils.db import get_db, log_activity

@pytest.fixture
def client():
    """Fixture pour créer un client de test"""
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    client = app.test_client()
    
    with client.session_transaction() as sess:
        sess['logged_in'] = True
        sess['user_id'] = "test_user_id"
    
    yield client

@pytest.fixture
def setup_test_activity():
    """Fixture pour créer des activités de test"""
    # Générer un ID utilisateur unique pour les tests
    user_id = f"user_{uuid.uuid4().hex[:8]}"
    
    # Enregistrer quelques activités de test
    try:
        log_activity(user_id, "create", "tickets", "Création d'un ticket de test")
        log_activity(user_id, "view", "inventory", "Consultation de l'inventaire")
        log_activity(user_id, "update", "tickets", "Mise à jour d'un ticket de test")
    except Exception as e:
        print(f"Erreur lors de l'enregistrement des activités de test: {e}")
    
    yield {
        "user_id": user_id
    }
    
    # Nettoyage après les tests
    try:
        get_db("DELETE FROM activity_logs WHERE user_id = %s", (user_id,))
    except Exception as e:
        print(f"Erreur lors du nettoyage des activités de test: {e}")

def test_log_activity():
    """Test de l'enregistrement des activités"""
    # Générer un ID utilisateur unique
    user_id = f"test_{uuid.uuid4().hex[:8]}"
    
    try:
        # Enregistrer une activité
        result = log_activity(user_id, "auth", "login", "Connexion au système")
        
        # Vérifier que l'enregistrement a réussi
        assert result is True
        
        # Vérifier que l'activité a été enregistrée dans la base de données
        activities = get_db("SELECT * FROM activity_logs WHERE user_id = %s AND action_type = 'auth'", (user_id,))
        
        assert activities is not None
        assert len(activities) > 0
        assert activities[0][1] == user_id  # Vérifier l'ID utilisateur
        assert activities[0][2] == "auth"   # Vérifier le type d'action
        
    except Exception as e:
        pytest.fail(f"Erreur lors du test d'enregistrement d'activité: {e}")
    finally:
        # Nettoyer après le test
        try:
            get_db("DELETE FROM activity_logs WHERE user_id = %s", (user_id,))
        except Exception as e:
            print(f"Erreur lors du nettoyage après test: {e}")

def test_get_user_activities(setup_test_activity):
    """Test de récupération des activités par utilisateur"""
    user_data = setup_test_activity
    
    try:
        # Récupérer les activités de l'utilisateur
        activities = get_db("SELECT * FROM activity_logs WHERE user_id = %s", (user_data["user_id"],))
        
        # Vérifier que les activités ont été récupérées
        assert activities is not None
        assert len(activities) >= 3
        
        # Vérifier que toutes les activités appartiennent à l'utilisateur
        for activity in activities:
            assert activity[1] == user_data["user_id"]  # user_id à l'index 1
    except Exception as e:
        pytest.fail(f"Erreur lors du test de récupération des activités par utilisateur: {e}")

def test_get_module_activities(setup_test_activity):
    """Test de récupération des activités par module"""
    user_data = setup_test_activity
    
    try:
        # Récupérer les activités du module tickets
        activities = get_db("SELECT * FROM activity_logs WHERE module = %s", ("tickets",))
        
        # Vérifier que des activités ont été récupérées
        assert activities is not None
        
        # Vérifier qu'au moins une activité correspond à l'utilisateur de test
        found = False
        for activity in activities:
            if activity[1] == user_data["user_id"]:  # user_id à l'index 1
                found = True
                break
        
        assert found is True
    except Exception as e:
        pytest.fail(f"Erreur lors du test de récupération des activités par module: {e}")

def test_get_activity_logs(setup_test_activity):
    """Test de récupération des logs d'activité"""
    user_data = setup_test_activity
    
    try:
        # Récupérer toutes les activités du système
        activities = get_db("SELECT * FROM activity_logs ORDER BY timestamp DESC LIMIT 50")
        
        # Vérifier qu'il y a des activités
        assert activities is not None
        
        # Vérifier si les activités de l'utilisateur de test sont présentes
        user_activities = get_db("SELECT * FROM activity_logs WHERE user_id = %s", (user_data["user_id"],))
        
        assert user_activities is not None
        assert len(user_activities) >= 3  # Au moins 3 activités ont été créées
    except Exception as e:
        pytest.fail(f"Erreur lors du test de récupération des logs: {e}")

def test_activity_routes(client):
    """Test des routes du module d'activité"""
    # Ces tests vérifient simplement que les routes répondent correctement

    # Test de la page principale d'activité
    response = client.get('/activity/')
    assert response.status_code in [200, 302]  # 200 OK ou 302 Redirect si non connecté
    
    # Test du tableau de bord
    response = client.get('/activity/dashboard')
    assert response.status_code in [200, 302]  # 200 OK ou 302 Redirect si non connecté
    
    # Test de l'affichage en direct
    response = client.get('/activity/live')
    assert response.status_code in [200, 302]  # 200 OK ou 302 Redirect si non connecté

@pytest.mark.skip(reason="Test d'export de fichier qui pourrait être instable en environnement de test")
def test_export_logs(client):
    """Test de l'export des logs d'activité"""
    response = client.get('/activity/export-logs')
    assert response.status_code in [200, 302]  # 200 OK ou 302 Redirect si non connecté
    
    # Si connecté, vérifier l'en-tête Content-Type
    if response.status_code == 200:
        assert response.headers.get('Content-Type') == 'text/csv'