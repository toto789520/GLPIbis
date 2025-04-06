@echo off
echo === Configuration de GLPIbis ===

REM Vérifier si le fichier .env existe, sinon copier le modèle
if not exist .env (
    echo Création du fichier .env à partir du modèle...
    copy .env.example .env
    echo Veuillez configurer le fichier .env selon vos besoins avant de continuer.
    echo Pour continuer avec les paramètres par défaut, appuyez sur une touche.
    pause > nul
)

REM Vérifier si le dossier config existe, sinon le créer
if not exist config (
    mkdir config
)

REM Vérifier si le fichier de configuration JSON existe, sinon le créer
if not exist config\conf.conf (
    echo Création du fichier de configuration...
    echo {> config\conf.conf
    echo   "IP_db": "db",>> config\conf.conf
    echo   "user_db": "glpiuser",>> config\conf.conf
    echo   "password_db": "glpipassword",>> config\conf.conf
    echo   "name_db": "glpidb">> config\conf.conf
    echo }>> config\conf.conf
    echo Fichier de configuration créé avec succès.
)

REM Démarrer l'application avec Docker Compose
echo Démarrage des conteneurs Docker...
docker-compose up -d

echo === Configuration terminée ===
echo L'application GLPIbis est accessible sur http://localhost:5000
echo phpMyAdmin est accessible sur http://localhost:8080
echo   - Utilisateur: root
echo   - Mot de passe: rootpassword (défini dans .env)
echo Pour arrêter l'application, exécutez 'docker-compose down'
pause