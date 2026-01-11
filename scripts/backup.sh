#!/bin/bash

# Script de sauvegarde quotidienne du projet GLPIBis

BACKUP_DIR="backups"
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/glpi_backup_${BACKUP_DATE}.tar.gz"
RETENTION_DAYS=30

echo "=== Sauvegarde GLPIBis - ${BACKUP_DATE} ==="

# Vérifier que Docker Compose est en cours d'exécution
if ! docker-compose ps | grep -q "Up"; then
    echo "⚠️  Attention: Les conteneurs ne sont pas tous actifs"
fi

# Créer le répertoire de sauvegarde s'il n'existe pas
mkdir -p "${BACKUP_DIR}"

# Sauvegarde de la base de données MySQL
echo "📊 Sauvegarde de la base de données..."
docker-compose exec -T mysql mysqldump \
    -u ${MYSQL_USER} -p${MYSQL_PASSWORD} \
    ${MYSQL_DATABASE} > "${BACKUP_DIR}/glpi_db_${BACKUP_DATE}.sql"

if [ $? -eq 0 ]; then
    echo "✓ Base de données sauvegardée"
else
    echo "❌ Erreur lors de la sauvegarde de la BD"
fi

# Sauvegarde des fichiers
echo "📁 Sauvegarde des fichiers GLPI..."
tar -czf "${BACKUP_FILE}" volumes/glpi volumes/mysql

if [ $? -eq 0 ]; then
    echo "✓ Fichiers sauvegardés: ${BACKUP_FILE}"
else
    echo "❌ Erreur lors de la sauvegarde des fichiers"
fi

# Suppression des anciennes sauvegardes
echo "🗑️  Suppression des sauvegardes de plus de ${RETENTION_DAYS} jours..."
find "${BACKUP_DIR}" -name "glpi_backup_*.tar.gz" -mtime +${RETENTION_DAYS} -delete
find "${BACKUP_DIR}" -name "glpi_db_*.sql" -mtime +${RETENTION_DAYS} -delete

echo ""
echo "=== ✓ Sauvegarde terminée ==="
echo "Fichiers de sauvegarde:"
ls -lh "${BACKUP_DIR}"/glpi_backup_*.tar.gz 2>/dev/null | tail -5
