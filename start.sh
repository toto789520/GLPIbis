#!/bin/bash

# Script de démarrage pour GLPIbis

echo "=== Configuration de GLPIbis ==="

# Vérifier si le fichier .env existe, sinon copier le modèle
if [ ! -f .env ]; then
  echo "Création du fichier .env à partir du modèle..."
  cp .env.example .env
  echo "Veuillez configurer le fichier .env selon vos besoins avant de continuer."
  echo "Pour continuer avec les paramètres par défaut, appuyez sur Entrée."
  read -p "Appuyez sur Entrée pour continuer ou Ctrl+C pour annuler..."
fi

# Vérifier si le fichier de configuration JSON existe, sinon le créer
if [ ! -f config/conf.conf ]; then
  echo "Création du fichier de configuration..."
  mkdir -p config
  cat > config/conf.conf << EOF
{
  "IP_db": "db",
  "user_db": "${MYSQL_USER:-glpiuser}",
  "password_db": "${MYSQL_PASSWORD:-glpipassword}",
  "name_db": "${MYSQL_DATABASE:-glpidb}"
}
EOF
  echo "Fichier de configuration créé avec succès."
fi

# Démarrer l'application avec Docker Compose
echo "Démarrage des conteneurs Docker..."
docker-compose up -d

echo "=== Configuration terminée ==="
echo "L'application GLPIbis est accessible sur http://localhost:5000"
echo "phpMyAdmin est accessible sur http://localhost:8080"
echo "  - Utilisateur: root"
echo "  - Mot de passe: ${MYSQL_ROOT_PASSWORD:-rootpassword} (défini dans .env)"
echo "Pour arrêter l'application, exécutez 'docker-compose down'"