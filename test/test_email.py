import pytest
import sys
import os
import re
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# Ajouter le dossier racine au chemin de recherche des modules
sys.path.append(project_root)
from onekey.auth import register_user
from utils.db import get_db

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
    # Créer un utilisateur
    email = "test_duplicate@example.com"
    password = "Password123!"
    
    try:
        # Créer le premier utilisateur
        user_id1 = register_user("Test User 1", "25", "1234567890", email, password)
        
        # Tenter de créer un deuxième utilisateur avec le même e-mail
        try:
            user_id2 = register_user("Test User 2", "30", "0987654321", email, password)
            pytest.fail("Le test aurait dû échouer avec un e-mail dupliqué")
        except ValueError:
            # C'est le comportement attendu
            pass
    finally:
        # Nettoyer après le test
        if 'user_id1' in locals() and user_id1:
            get_db("DELETE FROM USEUR WHERE ID = %s", (user_id1,))

def test_register_with_complex_password():
    """Test que l'enregistrement nécessite un mot de passe complexe"""
    email = "test_password@example.com"
    valid_password = "Password123!"
    invalid_passwords = [
        "password",  # pas de majuscule, pas de chiffre, pas de caractère spécial
        "PASSWORD123",  # pas de minuscule, pas de caractère spécial
        "Password",  # pas de chiffre, pas de caractère spécial
        "123456!"  # pas de lettre
    ]
    
    # Tester avec un mot de passe valide
    try:
        user_id = register_user("Test User", "25", "1234567890", email, valid_password)
        assert user_id is not None
        # Nettoyer
        get_db("DELETE FROM USEUR WHERE ID = %s", (user_id,))
    except ValueError as e:
        pytest.fail(f"L'enregistrement avec un mot de passe valide a échoué: {e}")
    
    # Tester avec des mots de passe invalides
    for password in invalid_passwords:
        try:
            user_id = register_user("Test User", "25", "1234567890", 
                                 f"test_{password}@example.com", password)
            get_db("DELETE FROM USEUR WHERE ID = %s", (user_id,))
            pytest.fail(f"Le test aurait dû échouer avec le mot de passe invalide: {password}")
        except ValueError:
            # C'est le comportement attendu
            pass