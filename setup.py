from utils.db import get_db

# créer la base de donner depuis la connettion exstanse pour la database

def set_up_database():
    # arder
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
        `gravite` NUMERIC NOT NULL,  # Correction de 'gravité' en 'gravite'
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
        CREATE TABLE IF NOT EXISTS USEUR (
        ID VARCHAR(255) NOT NULL,
        dete_de_creation VARCHAR(255),
        age INT,
        name VARCHAR(255) NOT NULL,
        tel VARCHAR(255),
        email VARCHAR(255) NOT NULL,
        hashed_password VARCHAR(255) NOT NULL
        );
    '''))
    print(get_db('''
        CREATE TABLE IF NOT EXISTS `materiel`( 
	    `Nom` Text NULL,
	    `catégorie` Text NULL,
	    `ID` Float NULL )
        ENGINE = InnoDB;
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

if __name__ == '__main__':
    print("Setting up database...")
    set_up_database()
    print("Database setup complete.")