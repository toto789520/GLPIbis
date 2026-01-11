## Nom du proget glpiBis

## Description
Glpibis dois géré les tickets d'incidents et de demandes de services pour une organisation. Il permet aux utilisateurs de soumettre des tickets, de suivre leur progression et de recevoir des notifications sur les mises à jour.

et aussi de gérer le parc informatique, les contrats, les licences et les fournisseurs.

## Fonctionnalités principales
- Gestion des tickets d'incidents et de demandes de services
- Suivi des tickets avec des statuts et des priorités
- Assignation des tickets aux techniciens automatiquement ou manuellement
- Base de connaissances pour les solutions courantes
- Notifications par e-mail pour les mises à jour des tickets
- Gestion du parc informatique (matériel, logiciels, etc.)
- Inventaire automatique des équipements réseau
- Ping et surveillance des équipements
- Gestion des contrats, licences et fournisseurs
- Rapports et statistiques sur les tickets et le parc informatique

## Infarastructure technique
- 3 Modules principaux pour docker : 
  - Serveur Web (Apache/Nginx)
  - Base de données (MySQL)
  - Application GLPI
- Utilisation de Docker Compose pour orchestrer les conteneurs
- Stockage persistant pour la base de données et les fichiers GLPI

## Technologies utilisées
- PHP pour le développement de l'application GLPI
- MySQL pour la gestion de la base de données
- Docker et Docker Compose pour la conteneurisation et l'orchestration