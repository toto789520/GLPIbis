from db import get_db

# créer la base de donner depuis la connettion exstanse pour la database

def set_up_database():
    # arder
    print(get_db('''
        CREATE TABLE `arder` (
        `name` TEXT NOT NULL,
        `typename` NUMERIC DEFAULT 0
        );
    '''))
    print(get_db('''
        CREATE TABLE `sesion_id` (
        `id_user` VARCHAR(255) UNIQUE NOT NULL,
        `sesion_id` VARCHAR(255) UNIQUE NOT NULL
        );
    '''))
    print(get_db('''
        CREATE TABLE `state` (
        `id_user` TEXT,
        `tiqué_créer` NUMERIC,
        `tiqué_partisipé` NUMERIC,
        `comm` NUMERIC
        );
    '''))
    print(get_db('''
        CREATE TABLE `test` (`test` TEXT);
    '''))
    print(get_db('''
        CREATE TABLE `tiqué` (
        `ID_tiqué` NUMERIC,
        `ID_user` NUMERIC NOT NULL,
        `date_open` TEXT NOT NULL,
        `date_close` TEXT,
        `descipition` TEXT NOT NULL,
        `titre` TEXT NOT NULL,
        `gavite` NUMERIC NOT NULL,
        `tag` TEXT,
        `open` INTEGER NOT NULL DEFAULT 1
        );
    '''))
    print(get_db('''
        CREATE TABLE `tiqué_type` (
        `name` TEXT NOT NULL,
        `typename` NUMERIC DEFAULT 0
        );
    '''))
    print(get_db('''
        CREATE TABLE USEUR (
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
        CREATE TABLE `materiel`( 
	    `Nom` Text NULL,
	    `catégorie` Text NULL,
	    `ID` Float NULL )
        ENGINE = InnoDB;
    '''))






set_up_database()