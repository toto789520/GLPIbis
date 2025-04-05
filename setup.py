from utils.db import get_db

# Créer la base de données depuis la connexion existante pour la base de données
def set_up_database():
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
        print(get_db('DROP TABLE IF EXISTS `tiqué_type`;'))
        print(get_db('DROP TABLE IF EXISTS `state`;'))
        print(get_db('DROP TABLE IF EXISTS `sesion_id`;'))
        print(get_db('DROP TABLE IF EXISTS `arder`;'))
        print(get_db('DROP TABLE IF EXISTS `test`;'))
    except Exception as e:
        print(f"Erreur lors de la suppression des tables: {str(e)}")

    # Création des tables de base
    print(get_db('''
        CREATE TABLE IF NOT EXISTS `arder` (
        `name` TEXT NOT NULL,
        `typename` NUMERIC DEFAULT 0
        );
    '''))
    print(get_db('''
        CREATE TABLE IF NOT EXISTS `sesion_id` (
        `id_user` VARCHAR(255) UNIQUE NOT NULL,
        `sesion_id` VARCHAR(255) UNIQUE NOT NULL
        );
    '''))
    print(get_db('''
        CREATE TABLE IF NOT EXISTS `state` (
        `id_user` TEXT,
        `tiqué_créer` NUMERIC,
        `tiqué_partisipé` NUMERIC,
        `comm` NUMERIC
        );
    '''))
    print(get_db('''
        CREATE TABLE IF NOT EXISTS `test` (`test` TEXT);
    '''))
    print(get_db('''
        CREATE TABLE IF NOT EXISTS `tiqué` (
        `ID_tiqué` TEXT NOT NULL,
        `ID_user` TEXT NOT NULL,
        `date_open` TEXT NOT NULL,
        `date_close` TEXT,
        `descipition` TEXT NOT NULL,
        `titre` TEXT NOT NULL,
        `gravite` NUMERIC NOT NULL,
        `tag` TEXT,
        `open` INTEGER NOT NULL DEFAULT 1
        );
    '''))
    print(get_db('''
        CREATE TABLE IF NOT EXISTS `tiqué_type` (
        `name` TEXT NOT NULL,
        `typename` NUMERIC DEFAULT 0
        );
    '''))
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

    # Table pour la localisation
    print(get_db('''
        CREATE TABLE IF NOT EXISTS `localisation` (
        `id` INT AUTO_INCREMENT PRIMARY KEY,
        `batiment` VARCHAR(255) NOT NULL,
        `etage` VARCHAR(50),
        `salle` VARCHAR(255),
        `description` TEXT
        );
    '''))

    # Recréation des tables d'inventaire dans le bon ordre

    # Tables de catégories pour l'inventaire
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

    # Table materiel avec la structure attendue
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

    # Table d'association entre tickets et matériel
    print(get_db('''
        CREATE TABLE IF NOT EXISTS `ticket_materiel` (
        `id` INT AUTO_INCREMENT PRIMARY KEY,
        `id_ticket` TEXT NOT NULL,
        `id_materiel` INT NOT NULL,
        `date_association` DATE NOT NULL,
        FOREIGN KEY (`id_materiel`) REFERENCES `materiel`(`id`) ON DELETE CASCADE
        );
    '''))

    # Créer la table sessions pour la gestion des sessions utilisateurs
    print(get_db('''
        CREATE TABLE IF NOT EXISTS `sessions` (
        `id` INT AUTO_INCREMENT PRIMARY KEY,
        `user_id` VARCHAR(255) NOT NULL,
        `token` VARCHAR(255) UNIQUE NOT NULL,
        `expiry_date` DATETIME NOT NULL,
        `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
        INDEX `idx_user_id` (`user_id`),
        INDEX `idx_token` (`token`)
        );
    '''))

    # Table pour les prêts
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

    # Table pour les interventions
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
