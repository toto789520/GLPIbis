1. Nom du projet
GLPIBis

2. Résumé / Description
Le projet GLPIBis vise à déployer et configurer une solution GLPI pour centraliser et optimiser la gestion du support informatique et du parc matériel. L'objectif est de remplacer l'actuel système de suivi par e-mails par une plateforme unique, traçable et automatisée pour améliorer la réactivité du service informatique et la satisfaction des utilisateurs.

3. Périmètre

Inclus : Gestion des incidents/demandes pour les postes de travail (Windows/macOS), serveurs (Windows/Linux), imprimantes. Inventaire automatique de ce parc. Gestion des contrats de maintenance associés.
Exclus (V1) : Gestion des assets mobiles (smartphones), gestion de la téléphonie VoIP, intégration avec le LDAP/Active Directory (envisagée pour V2).

4. Fonctionnalités par phase

Phase 1:
Gestion des tickets.
Notifications par e-mail.
Inventaire du parc par import CSV.
Gestion simple des contrats.
Phase 2:
Déploiement de GLPI-Agent pour l'inventaire automatique et Assetement automatique des tickets.
Mise en place d'une base de connaissances.
Création de rapports et tableaux de bord.
Étude pour l'intégration LDAP.

5. Infrastructure technique cible

Orchestration : Docker Compose sur un serveur dédié (Debian 12).
Conteneurs :
Serveur Web : Nginx (avec reverse-proxy pour HTTPS)
Base de données : MySQL 8.0
Application : GLPI 10.x (image officielle)
Persistance des données : Volumes Docker pour la base de données et les fichiers de l'application.
Sauvegarde : Script de sauvegarde quotidienne des volumes Docker vers un stockage externe.

6. Technologies clés

Application : PHP 8.1+
Base de données : MySQL 8.0
Conteneurisation : Docker, Docker Compose
Réseau : Nginx, Let's Encrypt (pour SSL)