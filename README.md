# GLPIbis

GLPIbis est une application de gestion de tickets et d'inventaire IT, inspirée par GLPI.

## Fonctionnalités

- Gestion des tickets de support
- Système d'authentification sécurisé
- Génération de codes QR pour le matériel
- Interface utilisateur intuitive
- Base de données MySQL pour le stockage

## Installation

1. Cloner le repository
2. Installer les dépendances : `pip install -r requirements.txt`
3. Configurer le fichier `.env`
4. Lancer l'application : `python app.py`

## TODO
- Implémenter le système de chat/communication pour les tickets
- Assurer une traçabilité appropriée des interactions avec les tickets
- Tester le système de tickets pour la fonctionnalité et la performance

## Technologies utilisées

- Flask 2.0.1
- MySQL via PyMySQL
- BCrypt pour la sécurité
- QRCode pour la gestion des assets
