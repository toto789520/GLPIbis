import json
import os
from utils.db_manager import get_db

# Charger la configuration depuis conf.conf
CONFIG_FILE = 'config/conf.conf'

def load_config():
    if not os.path.exists(CONFIG_FILE):
        raise FileNotFoundError(f"Le fichier de configuration {CONFIG_FILE} est introuvable.")
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def set_up_database():
    config = load_config()
    db_type = config.get('db_type', 'sqlite')

    if db_type == 'sqlite':
        print("Configuration pour SQLite détectée.")
    elif db_type == 'mysql':
        print("Configuration pour MySQL détectée.")
    else:
        raise ValueError(f"Type de base de données non supporté : {db_type}")

    # Supprimer d'abord les tables avec des contraintes de clé étrangère dans le bon ordre
    try:
        print(get_db('DROP TABLE IF EXISTS `intervention`;'))
        print(get_db('DROP TABLE IF EXISTS `pret`;'))
        print(get_db('DROP TABLE IF EXISTS `ticket_materiel`;'))
        print(get_db('DROP TABLE IF EXISTS `materiel`;'))
        print(get_db('DROP TABLE IF EXISTS `sous_sous_categorie`;'))
        print(get_db('DROP TABLE IF EXISTS `sous_categorie`;'))
        print(get_db('DROP TABLE IF EXISTS `categorie`;'))
        print(get_db('DROP TABLE IF EXISTS `localisation`;'))
        print(get_db('DROP TABLE IF EXISTS `USEUR`;'))
        print(get_db('DROP TABLE IF EXISTS `tiqué`;'))
    except Exception as e:
        print(f"Erreur lors de la suppression des tables: {str(e)}")

    # Création des tables nécessaires
    print(get_db('''
        CREATE TABLE IF NOT EXISTS `USEUR` (
        `ID` VARCHAR(255) NOT NULL PRIMARY KEY,
        `dete_de_creation` VARCHAR(255),
        `age` INT,
        `name` VARCHAR(255) NOT NULL,
        `tel` VARCHAR(255),
        `email` VARCHAR(255) NOT NULL,
        `hashed_password` VARCHAR(255) NOT NULL
        );
    '''))

    print(get_db('''
        CREATE TABLE IF NOT EXISTS `tiqué` (
        `ID_tiqué` INTEGER PRIMARY KEY AUTOINCREMENT,
        `id_creator` VARCHAR(255) NOT NULL,
        `titre` VARCHAR(255) NOT NULL,
        `date_creation` DATE NOT NULL,
        `date_resolution` DATE,
        `date_cloture` DATE,
        `description` TEXT NOT NULL,
        `priorite` INTEGER NOT NULL DEFAULT 1,
        `tags` TEXT,
        `statut` INTEGER NOT NULL DEFAULT 1,
        FOREIGN KEY (`id_creator`) REFERENCES `USEUR`(`ID`)
        );
    '''))

    print(get_db('''
        CREATE TABLE IF NOT EXISTS `localisation` (
        `id` INT AUTO_INCREMENT PRIMARY KEY,
        `batiment` VARCHAR(255) NOT NULL,
        `etage` VARCHAR(50),
        `salle` VARCHAR(255),
        `description` TEXT
        );
    '''))

    print(get_db('''
        CREATE TABLE IF NOT EXISTS `categorie` (
        `id` INT AUTO_INCREMENT PRIMARY KEY,
        `nom` VARCHAR(255) NOT NULL,
        `description` TEXT
        );
    '''))

    print(get_db('''
        CREATE TABLE IF NOT EXISTS `sous_categorie` (
        `id` INT AUTO_INCREMENT PRIMARY KEY,
        `nom` VARCHAR(255) NOT NULL,
        `description` TEXT,
        `id_categorie` INT NOT NULL,
        FOREIGN KEY (`id_categorie`) REFERENCES `categorie`(`id`) ON DELETE CASCADE
        );
    '''))

    print(get_db('''
        CREATE TABLE IF NOT EXISTS `sous_sous_categorie` (
        `id` INT AUTO_INCREMENT PRIMARY KEY,
        `nom` VARCHAR(255) NOT NULL,
        `description` TEXT,
        `id_sous_categorie` INT NOT NULL,
        FOREIGN KEY (`id_sous_categorie`) REFERENCES `sous_categorie`(`id`) ON DELETE CASCADE
        );
    '''))

    print(get_db('''
        CREATE TABLE IF NOT EXISTS `materiel` (
        `id` INT AUTO_INCREMENT PRIMARY KEY,
        `nom` TEXT NOT NULL,
        `categorie` INT NOT NULL,
        `sous_categorie` INT NOT NULL,
        `sous_sous_categorie` INT NOT NULL,
        `date_creation` DATE NOT NULL,
        `qr_code` VARCHAR(50) UNIQUE NOT NULL,
        `id_localisation` INT,
        FOREIGN KEY (`categorie`) REFERENCES `categorie`(`id`),
        FOREIGN KEY (`sous_categorie`) REFERENCES `sous_categorie`(`id`),
        FOREIGN KEY (`sous_sous_categorie`) REFERENCES `sous_sous_categorie`(`id`),
        FOREIGN KEY (`id_localisation`) REFERENCES `localisation`(`id`)
        );
    '''))

    print(get_db('''
        CREATE TABLE IF NOT EXISTS `ticket_materiel` (
        `id` INTEGER PRIMARY KEY AUTOINCREMENT,
        `id_ticket` INTEGER NOT NULL,
        `id_materiel` INTEGER NOT NULL,
        `date_association` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (`id_ticket`) REFERENCES `tiqué`(`ID_tiqué`),
        FOREIGN KEY (`id_materiel`) REFERENCES `materiel`(`id`)
        );
    '''))

    print(get_db('''
        CREATE TABLE IF NOT EXISTS `pret` (
        `id` INT AUTO_INCREMENT PRIMARY KEY,
        `id_materiel` INT NOT NULL,
        `id_emprunteur` VARCHAR(255) NOT NULL,
        `date_emprunt` DATETIME DEFAULT CURRENT_TIMESTAMP,
        `date_retour_prevue` DATETIME NOT NULL,
        `date_retour` DATETIME,
        `notes` TEXT,
        `statut` ENUM('en_cours', 'retourne', 'en_retard') DEFAULT 'en_cours',
        FOREIGN KEY (`id_materiel`) REFERENCES `materiel`(`id`),
        FOREIGN KEY (`id_emprunteur`) REFERENCES `USEUR`(`ID`)
        );
    '''))

    print(get_db('''
        CREATE TABLE IF NOT EXISTS `intervention` (
        `id` INT AUTO_INCREMENT PRIMARY KEY,
        `id_materiel` INT NOT NULL,
        `id_technicien` VARCHAR(255) NOT NULL,
        `type` VARCHAR(50) NOT NULL,
        `description` TEXT NOT NULL,
        `date_debut` DATETIME DEFAULT CURRENT_TIMESTAMP,
        `date_fin` DATETIME,
        `statut` ENUM('en_cours', 'termine') DEFAULT 'en_cours',
        FOREIGN KEY (`id_materiel`) REFERENCES `materiel`(`id`),
        FOREIGN KEY (`id_technicien`) REFERENCES `USEUR`(`ID`)
        );
    '''))
