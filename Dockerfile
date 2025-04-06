FROM python:3.9-slim

WORKDIR /app

# Installation des dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copie des fichiers de dépendances pour les installer
COPY requirements.txt .

# Installation des dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source de l'application
COPY . .

# Création des dossiers nécessaires s'ils n'existent pas
RUN mkdir -p config static/qr_codes

# Exposition du port sur lequel l'application Flask s'exécutera
EXPOSE 5000

# Commande pour démarrer l'application
CMD ["python", "app.py"]