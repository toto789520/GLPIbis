FROM python:3.11-slim

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code de l'application
COPY . .

# Créer le dossier pour les uploads
RUN mkdir -p /app/uploads/bills

# Exposer le port Flask
EXPOSE 5000

# Variables d'environnement par défaut
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1

# Volume pour persister les fichiers uploadés
VOLUME ["/app/uploads"]

# Commande de démarrage avec Gunicorn pour la production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app:app"]
