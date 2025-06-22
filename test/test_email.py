import pytest
import sys
import os
import re
import uuid
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# Ajouter le dossier racine au chemin de recherche des modules
sys.path.append(project_root)
from onekey.auth import register_user
from utils.db_manager import get_db

# Fonction utilitaire pour valider l'e-mail
def is_valid_email(email):
    """Vérifie si l'e-mail respecte un format basique"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def test_email_basic_format():
    """Test de validation basique du format d'email"""
    # Test avec différents formats d'e-mail
    valid_emails = [
        "test.email@example.com",
        "user123@gmail.com",
        "firstname.lastname@domain.co.uk"
    ]
    
    invalid_emails = [
        "test.email@",  # sans domaine
        "test.email.example.com",  # sans @
        "test..email@example",  # double point
        "@example.com"  # sans nom local
    ]
    
    # Vérification avec notre fonction utilitaire
    for email in valid_emails:
        assert is_valid_email(email), f"L'e-mail {email} devrait être considéré comme valide"
        
    for email in invalid_emails:
        assert not is_valid_email(email), f"L'e-mail {email} devrait être considéré comme invalide"

def test_register_with_duplicate_email():
    """Test que l'enregistrement avec un e-mail dupliqué échoue"""
    email = "test_duplicate@example.com"
    password = "Password123!"
    user_id1 = None

    # Nettoyage préalable pour éviter les conflits de tests précédents
    get_db("DELETE FROM USEUR WHERE EMAIL = ?", (email,))

    try:
        # Premier enregistrement
        user_id1 = register_user("Test User 1", "25", "1234567890", email, password)
        assert user_id1 is not None

        # Deuxième enregistrement avec le même email
        with pytest.raises(ValueError) as excinfo:
            register_user("Test User 2", "30", "0987654321", email, password)
        assert "existe déjà" in str(excinfo.value)

    finally:
        if user_id1:
            get_db("DELETE FROM USEUR WHERE ID = ?", (user_id1,))

def test_register_with_complex_password():
    """Test que l'enregistrement nécessite un mot de passe complexe"""
    test_id = str(uuid.uuid4())
    email = f"test_password_{test_id}@example.com"
    valid_password = "Password123!"
    user_id = None

    try:
        user_id = register_user("Test User", "25", "1234567890", email, valid_password)
        assert user_id is not None

        # Test des mots de passe invalides
        invalid_passwords = ["password", "PASSWORD123", "Password", "123456!"]
        for invalid_pass in invalid_passwords:
            with pytest.raises(ValueError) as excinfo:
                register_user("Test User", "25", "1234567890", 
                            f"test_{invalid_pass}@example.com", invalid_pass)
            assert "mot de passe" in str(excinfo.value).lower()

    finally:
        if user_id:
            get_db("DELETE FROM USEUR WHERE ID = ?", (user_id,))