import os
import tempfile
import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
    client = app.test_client()

    yield client

    # Nettoyage après les tests
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        for file in os.listdir(app.config['UPLOAD_FOLDER']):
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], file))
        os.rmdir(app.config['UPLOAD_FOLDER'])

def test_add_hardware_with_photo(client):
    """Test de l'ajout de matériel avec une photo"""
    data = {
        'nom': 'Test Matériel',
        'categorie': '1',
        'sous_categorie': '1',
        'sous_sous_categorie': '1',
        'date_creation': '2023-01-01',
        'qr_code': 'TEST1234',
        'description': 'Description de test'
    }

    # Ajout d'un fichier image simulé
    with tempfile.NamedTemporaryFile(suffix='.jpg') as temp_file:
        temp_file.write(b"fake image data")
        temp_file.seek(0)
        data['photo'] = (temp_file, 'test.jpg')

        response = client.post('/inventory/add_hardware', data=data, content_type='multipart/form-data')

    assert response.status_code == 302  # Redirection après ajout
    assert b"Matériel ajouté avec succès!" in response.data