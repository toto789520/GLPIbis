# Documentation GLPIbis

## Architecture du système

### Structure des dossiers
```
GLPIbis/
├── app.py           # Point d'entrée de l'application
├── static/          # Fichiers statiques (CSS, JS)
├── templates/       # Templates HTML
├── models/          # Modèles de données
└── utils/          # Utilitaires et helpers
```

### Base de données
La base de données MySQL contient les tables suivantes :
- users : Gestion des utilisateurs
- tickets : Suivi des tickets
- assets : Inventaire du matériel
- categories : Catégories de tickets/matériel

### API Endpoints
- `/api/tickets` : Gestion des tickets
- `/api/users` : Gestion des utilisateurs
- `/api/assets` : Gestion du matériel
- `/api/qr` : Génération des codes QR

### Sécurité
- Authentification via bcrypt
- Sessions sécurisées
- Protection CSRF
- Validation des entrées

## Guide de développement

### Configuration
1. Créer un fichier `.env` avec :
   ```
   DB_HOST=localhost
   DB_USER=user
   DB_PASSWORD=password
   DB_NAME=glpibis
   SECRET_KEY=your_secret_key
   ```

### Tests
- Lancer les tests : `pytest tests/`
- Coverage : `pytest --cov=app tests/`