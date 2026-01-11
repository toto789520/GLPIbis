#!/bin/bash

# Script d'arrêt du projet GLPIBis

echo "=== Arrêt du projet GLPIBis ==="

# Arrêt des conteneurs
echo "🛑 Arrêt des conteneurs..."
docker-compose down

if [ $? -eq 0 ]; then
    echo "✓ Conteneurs arrêtés avec succès"
else
    echo "❌ Erreur lors de l'arrêt des conteneurs"
    exit 1
fi

echo ""
echo "=== ✓ GLPIBis arrêté ==="
