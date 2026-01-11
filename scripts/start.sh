#!/bin/bash

# Script de démarrage du projet GLPIBis

echo "=== Démarrage du projet GLPIBis ==="

# Chargement des variables d'environnement
if [ ! -f .env ]; then
    echo "❌ Erreur: Le fichier .env est manquant!"
    exit 1
fi

echo "✓ Fichier .env trouvé"

# Création des répertoires s'ils n'existent pas
mkdir -p volumes/mysql volumes/glpi backups nginx/ssl

echo "✓ Répertoires vérifiés"

# Démarrage des conteneurs
echo "📦 Démarrage des conteneurs Docker Compose..."
docker-compose up -d

if [ $? -eq 0 ]; then
    echo "✓ Conteneurs démarrés avec succès"
else
    echo "❌ Erreur au démarrage des conteneurs"
    exit 1
fi

# Attendre que les services soient prêts
echo "⏳ Attente de l'initialisation des services..."
sleep 10

# Vérification du statut des conteneurs
echo "📋 Statut des conteneurs:"
docker-compose ps

echo ""
echo "=== ✓ GLPIBis est prêt ==="
echo ""
echo "Accès à l'application:"
echo "  HTTP:  http://localhost"
echo "  HTTPS: https://localhost"
echo ""
echo "Configuration requise:"
echo "  - Mettre à jour le fichier .env avec vos paramètres"
echo "  - Configurer les certificats SSL dans nginx/ssl/"
echo "  - Accéder à l'installation de GLPI et configurer la base de données"
