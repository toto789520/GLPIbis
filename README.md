# GLPIBis - Gestion du Support Informatique

## 📋 Description

GLPIBis est une plateforme centralisée pour la gestion du support informatique et du parc matériel basée sur **GLPI 10.x**.

### Objectifs
- Remplacer le suivi par e-mails par une plateforme unique et traçable
- Optimiser la gestion des incidents/demandes
- Automatiser l'inventaire du parc informatique
- Gérer les contrats de maintenance
- Améliorer la réactivité du service IT

## 🏗️ Architecture

### Infrastructure
- **Orchestration**: Docker Compose
- **Serveur Web**: Nginx (reverse-proxy, HTTPS)
- **Application**: GLPI 10.x (PHP 8.1+)
- **Base de données**: MySQL 8.0
- **OS Cible**: Debian 12

### Services
```
┌─────────────────────────────────────────┐
│         Utilisateurs / Clients          │
└────────────────┬────────────────────────┘
                 │
        ┌────────▼────────┐
        │   Nginx/HTTPS   │
        └────────┬────────┘
                 │
        ┌────────▼────────────┐
        │   GLPI (PHP-FPM)    │
        └────────┬────────────┘
                 │
        ┌────────▼────────┐
        │    MySQL 8.0    │
        └─────────────────┘
```

## 📁 Structure du Projet

```
reglpi/
├── docker-compose.yml          # Orchestration des services
├── .env                        # Variables d'environnement
├── docker/                     # Fichiers Docker
│   ├── Dockerfile.glpi        # Image GLPI personnalisée
│   └── mysql/
│       └── init.sql           # Initialisation BD
├── nginx/                      # Configuration Nginx
│   ├── nginx.conf             # Configuration générale
│   ├── glpi.conf              # Configuration proxy GLPI
│   └── ssl/                   # Certificats SSL
├── scripts/                    # Scripts utilitaires
│   ├── start.sh               # Démarrage
│   ├── stop.sh                # Arrêt
│   └── backup.sh              # Sauvegarde
├── volumes/                    # Données persistantes
│   ├── glpi/                  # Fichiers GLPI
│   └── mysql/                 # Base de données
├── backups/                    # Sauvegardes
├── rootV1.md                  # Spécifications V1
└── rootV2 - Final.md          # Spécifications V2 (en cours)
```

## 🚀 Démarrage Rapide

### Prérequis
- Docker et Docker Compose
- Au minimum 4GB RAM disponible
- Port 80 et 443 disponibles

### Installation

1. **Cloner / Copier le projet**
```bash
cd reglpi
```

2. **Configurer les variables d'environnement**
```bash
cp .env.example .env
# Éditer .env avec vos paramètres
```

3. **Démarrer les services**
```bash
# Sous Linux/macOS
chmod +x scripts/*.sh
./scripts/start.sh

# Sous Windows (PowerShell)
docker-compose up -d
```

4. **Vérifier le statut**
```bash
docker-compose ps
```

## 🔐 Configuration SSL/HTTPS

### Option 1: Let's Encrypt (Recommandé)
```bash
certbot certonly --standalone -d your-domain.com
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/cert.pem
cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/key.pem
```

### Option 2: Certificat Auto-Signé (Dev/Test)
```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout nginx/ssl/key.pem \
  -out nginx/ssl/cert.pem
```

## 🛢️ Gestion de la Base de Données

### Sauvegarde manuelle
```bash
docker-compose exec mysql mysqldump \
  -u glpi_user -pGlpiPassword123! glpi_db > backup.sql
```

### Restauration
```bash
docker-compose exec -T mysql mysql \
  -u glpi_user -pGlpiPassword123! glpi_db < backup.sql
```

### Sauvegarde automatique
```bash
# Ajouter à crontab (Linux)
0 2 * * * /path/to/reglpi/scripts/backup.sh
```

## 📊 Accès à l'Application

- **URL**: https://your-domain.com
- **Port HTTP**: 80 → 8080 (redirection HTTPS)
- **Port HTTPS**: 443

## 🔧 Configuration GLPI

Après le premier démarrage, accédez à l'interface d'installation et configurez:
1. La base de données (MySQL)
2. Les paramètres de l'application
3. Les utilisateurs administrateurs
4. Les paramètres de notification

## 📈 Phases de Développement

### Phase 1 (V1 - En cours)
- ✅ Gestion des tickets
- ✅ Notifications par e-mail
- ✅ Inventaire par import CSV
- ✅ Gestion simple des contrats

### Phase 2 (V2 - Envisagée)
- 🔄 GLPI-Agent pour inventaire automatique
- 🔄 Base de connaissances
- 🔄 Rapports et tableaux de bord
- 🔄 Intégration LDAP/Active Directory

## 📚 Documentation Complémentaire

- [GLPI Official](https://glpi-project.org)
- [Docker Compose Docs](https://docs.docker.com/compose/)
- [Nginx Docs](https://nginx.org/docs/)
- [MySQL 8.0 Docs](https://dev.mysql.com/doc/)

## 🤝 Maintenance

### Logs
```bash
# Tous les services
docker-compose logs -f

# Service spécifique
docker-compose logs -f glpi
docker-compose logs -f mysql
docker-compose logs -f nginx
```

### Redémarrage
```bash
docker-compose restart
```

### Arrêt complet
```bash
./scripts/stop.sh
# ou
docker-compose down
```

## 🐛 Troubleshooting

| Problème | Solution |
|----------|----------|
| Port 80/443 déjà utilisé | Modifier `NGINX_PORT` et `NGINX_SSL_PORT` dans `.env` |
| Erreur de connexion BD | Vérifier les credentials dans `.env` |
| Certificat SSL invalide | Régénérer le certificat ou utiliser Let's Encrypt |
| Espace disque insuffisant | Nettoyer les anciens logs: `docker system prune` |

## 📝 Notes de Version

- **Version GLPI**: 10.0
- **PHP**: 8.1+
- **MySQL**: 8.0
- **Date**: 11 Janvier 2026

## 📞 Support

Pour toute question ou problème, consultez:
1. Les logs: `docker-compose logs`
2. La documentation GLPI officielle
3. Les fichiers de spécification (rootV2 - Final.md)
