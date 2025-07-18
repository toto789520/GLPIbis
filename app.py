import sys
import os

import sys
import os
import shutil
import atexit
from multiprocessing import Process, Queue, freeze_support
from state_handler import StateHandler  # nouveau fichier à créer

# Ajouter le répertoire racine au path Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from utils.logger import app_logger as logger
from utils.db_manager import init_db_manager, get_tables_list, get_db, DBManager
from utils.state_manager import state_manager
from datetime import datetime
from tickets.ticket_service import get_ticket_list
import atexit
from onekey import auth

# Variables globales pour la gestion des états
state_handler = StateHandler()
process_queue = Queue()

# Variable globale pour gérer l'état de pause de l'application
app_paused = False
app_paused_status = "Application en pause"
app_paused_message = "Application en pause pour maintenance ou mise à jour."

def init_db():
    """Initialise la base de données"""
    try:
        logger.info("Tentative d'initialisation de la base de données...")
        
        # Nettoyer les anciennes bases de données si elles existent
        cleanup_old_databases()

        # Initialisation du gestionnaire de base de données
        logger.info("Initialisation du gestionnaire de base de données pour SQLite")
        # Utilisation de la fonction init_db_manager pour initialiser la base de données
        db_manager = init_db_manager('sqlite')

        # Vérification de la structure des tables
        logger.info("Vérification de la structure des tables de la base de données")
        db_manager.verify_table_structure()
        logger.info("Structure des tables vérifiée avec succès")

        return db_manager
    except Exception as e:
        logger.error(f"ERREUR d'initialisation de la base de données: {e}")
        raise

def cleanup_old_databases():
    """Nettoie les anciennes bases de données pour utiliser uniquement glpibis.db"""
    try:
        project_root = os.getcwd()
        target_db = os.path.join(project_root, 'glpibis.db')
        
        # Liste des fichiers de base de données à supprimer
        old_db_files = ['db', 'data', 'database.sqlite', 'glpi.db', 'app.db']
        
        for db_file in old_db_files:
            db_path = os.path.join(project_root, db_file)
            if os.path.exists(db_path):
                try:
                    if os.path.isfile(db_path):
                        os.remove(db_path)
                        logger.info(f"Ancien fichier de base de données supprimé: {db_file}")
                    elif os.path.isdir(db_path):
                        import shutil
                        shutil.rmtree(db_path)
                        logger.info(f"Ancien répertoire de base de données supprimé: {db_file}")
                except Exception as e:
                    logger.warning(f"Impossible de supprimer {db_file}: {e}")
        
        logger.info("Nettoyage des anciennes bases de données terminé")
        
    except Exception as e:
        logger.warning(f"Erreur lors du nettoyage des bases de données: {e}")

# Initialisation de la base de données au démarrage
try:
    db_manager_instance = init_db()
    logger.info("Base de données initialisée avec succès")
    logger.info(f"Liste des tables Créées/Trouver : {get_tables_list()}")
    logger.info("=== BASE DE DONNÉES INITIALISÉE ===")
except Exception as e:
    logger.error(f"Impossible d'initialiser la base de données: {e}")
    sys.exit(1)

#lanch SOS mode 
try:
    import qrcode
except ImportError:
    logger.warning("Module 'qrcode' non disponible. Certaines fonctionnalités peuvent être limitées.")

# Modification de la fonction StartSOSMode pour éviter l'utilisation de 'flash' en dehors du contexte de requête
def StartSOSMode(app=None):
    """Active le mode SOS pour l'application"""
    logger.warning("\033[31m !===== MODE SOS ACTIVÉ =====! \033[0m")
    global app_paused, app_paused_status, app_paused_message
    app_paused = True
    app_paused_status = "Mode SOS activé"
    app_paused_message = "L'application fonctionne en mode dégradé. Certaines fonctionnalités peuvent être indisponibles."
    if app:
        app.config['SOS_MODE'] = True
        with app.app_context():  # Ajout d'un contexte d'application pour utiliser 'flash'
            flash("L'application fonctionne en mode dégradé. Certaines fonctionnalités sont limitées.", "warning")
    

def create_app():
    """Factory pour créer l'application Flask"""
    try:
        logger.info("=== DÉMARRAGE DE L'APPLICATION GLPIBIS ===")
        app = Flask(__name__)
        app.secret_key = "your-secret-key-here-change-this-in-production"

        def cleanup():
            """Fonction de nettoyage à la fermeture"""
            logger.info("======= ARRÊT DE L'APPLICATION =======")
            state_manager.stop()
            
        # Enregistrer la fonction cleanup avant d'initialiser state_manager
        atexit.register(cleanup)
        
        # Initialisation sécurisée du state_manager
        try:
            state_manager.initialize()
            if not app.debug:  # Ne démarrer le state_manager qu'en production
                state_manager.start()
        except Exception as e:
            logger.error(f"Erreur d'initialisation du state_manager: {e}")
            StartSOSMode(app)

        # Context processor pour rendre 'now' disponible dans tous les templates
        @app.context_processor
        def inject_now():
            def safe_url_for(endpoint, **values):
                """Version sécurisée de url_for qui ne lève pas d'erreur si l'endpoint n'existe pas"""
                try:
                    return url_for(endpoint, **values)
                except Exception:
                    # Si l'endpoint n'existe pas, retourner '#' ou une URL par défaut
                    flash(f"Erreur: L'endpoint '{endpoint}' n'existe pas.", 'error')
                    logger.error(f"Erreur lors de la génération de l'URL pour l'endpoint '{endpoint}' avec les valeurs {values}")
                    return '#'
            return {
                'now': datetime.now(),
                'safe_url_for': safe_url_for
            }        
        @app.before_request
        def validate_session_token():
            # Vérification du token de session avant chaque requête (sauf pour les routes publiques)
            public_routes = {'login', 'register', 'static', 'service_worker', 'service_worker_alt', 'favicon', 'robots', 'waiting', 'health_check'}
            if request.endpoint in public_routes or request.endpoint is None:
                return
            
            if 'token' in session:
                user_id = auth.validate_session(session['token'])
                if user_id:
                    # Mettre à jour l'ID utilisateur dans la session
                    session['user_id'] = user_id
                    return None
                else:
                    logger.warning(f"Session invalide pour l'utilisateur {session.get('user_id')}")
                    session.clear()
                    flash('Session expirée, veuillez vous reconnecter', 'error')
                    return redirect(url_for('login'))
            else:
                logger.debug("Aucun token de session trouvé")
                session.clear()
                return redirect(url_for('login'))
        
        # Routes principales
        @app.route('/')
        def index():
            return render_template('index.html')
          # Route spéciale pour la page d'attente
        @app.route('/waiting')
        def waiting():
            """Page d'attente lors des redémarrages"""
            return render_template('waiting.html')
          # Route pour servir le service worker
        @app.route('/sw.js')
        def service_worker():
            """Service worker pour la gestion offline"""
            from flask import send_from_directory
            return send_from_directory('static', 'sw.js', mimetype='application/javascript')
        
        # Route alternative pour le service worker
        @app.route('/static/sw.js')
        def service_worker_alt():
            """Service worker pour la gestion offline (route alternative)"""
            from flask import send_from_directory
            return send_from_directory('static', 'sw.js', mimetype='application/javascript')
        
        # Nettoyer à la fermeture
        atexit.register(cleanup)
        
        def cleanup():
            logger.info("======= ARRÊT DE L'APPLICATION =======")
            state_manager.stop()
        
        # Route pour vérifier si le serveur est disponible
        @app.route('/health')
        def health_check():
            """Point de contrôle rapide pour vérifier si l'application est disponible"""
            state = state_manager.get_state()
            return {
                'status': app_paused_status if app_paused else 'ok',
                'info': app_paused_message if app_paused else '',
                'tickets_count': state.get('tickets_count', 0),
                'active_users': state.get('active_users', 0),
                'last_update': state.get('last_update', 0)
            }

        # Route pour mettre l'application en pause
        @app.route('/pause')
        def pause():
            global app_paused
            if 'user_id' not in session:
                logger.warning("Tentative de mise en pause sans utilisateur connecté")
                flash('Vous devez être connecté pour mettre l\'application en pause', 'error')
                return redirect(url_for('login'))
            if app_paused:
                logger.info("L'application est déjà en pause - redémarrage")
                app_paused = False
                logger.info("Application redémarrée")
                return {'status': 'resumed'}
            app_paused = True
            logger.info("Application mise en pause")
            return {'status': 'paused'}

        @app.route('/login', methods=['GET', 'POST'])
        def login():
            logger.debug("Route /login appelée")
            
            if request.method == 'POST':
                logger.debug("Méthode POST détectée")
                email = request.form.get('email')  # Changé de 'username' à 'email'
                password = request.form.get('password')
                
                logger.debug(f"Identifiants reçus - Email: {email}")

                if email and password:
                    user_connected = auth.login_user(email, password)
                    if user_connected['status'] == 'error':
                        logger.error(f"Erreur de connexion pour {email}: {user_connected['message']}")
                        flash(user_connected['message'], 'error')
                        return render_template('login.html')
                    logger.debug(f"Résultat de la connexion: {user_connected}")
                    if not user_connected:
                        flash('Identifiants incorrects', 'error')
                        logger.warning(f"Échec de la connexion pour {email}")
                        return render_template('login.html')
                    else:
                        logger.info(f"Utilisateur connecté: {user_connected['user_id']}")
                        session['token'] = user_connected['token']
                        session['role'] = user_connected.get('role', 'user')
                    return redirect(url_for('dashboard'))
                else:
                    flash('Email et mot de passe requis', 'error')
                    logger.warning("Tentative de connexion avec des champs vides")
            
            logger.debug("Rendu du template login.html")
            return render_template('login.html')
        
        def get_dashboard_stats():
            """Récupère les statistiques pour le tableau de bord"""
            try:
                stats = {
                    'tickets_ouverts': 0,
                    'tickets_urgents': 0,
                    'tickets_resolus': 0,
                    'tickets_en_attente': 0,
                    'temps_moyen_resolution': 'N/A'
                }
                
                # Tickets ouverts
                open_cursor = get_db("SELECT COUNT(*) FROM tiqué WHERE open = 1")
                open_tickets = open_cursor[0] if open_cursor else None
                stats['tickets_ouverts'] = open_tickets[0] if open_tickets else 0
                
                # Tickets urgents
                urgent_cursor = get_db("SELECT COUNT(*) FROM tiqué WHERE open = 1 AND gravite <= 2")
                urgent_tickets = urgent_cursor[0] if urgent_cursor else None
                stats['tickets_urgents'] = urgent_tickets[0] if urgent_tickets else 0
                
                # Tickets résolus cette semaine
                resolved_cursor = get_db("""
                    SELECT COUNT(*) FROM tiqué 
                    WHERE open = 0 
                    AND date_close >= date('now', '-7 days')
                """)
                resolved_tickets = resolved_cursor[0] if resolved_cursor else None
                stats['tickets_resolus'] = resolved_tickets[0] if resolved_tickets else 0
                
                # Tickets en attente
                pending_cursor = get_db("SELECT COUNT(*) FROM tiqué WHERE date_open <= date('now', '-3 days') AND open = 1")
                pending_tickets = pending_cursor[0] if pending_cursor else None
                stats['tickets_en_attente'] = pending_tickets[0] if pending_tickets else 0
                
                # Temps moyen de résolution
                avg_cursor = get_db("""
                    SELECT AVG(julianday(date_close) - julianday(date_open)) * 24 * 60 as avg_minutes
                    FROM tiqué
                    WHERE open = 0 AND date_close IS NOT NULL
                """)
                avg_time = avg_cursor[0] if avg_cursor else None
                
                if avg_time and avg_time[0]:
                    minutes = int(avg_time[0])
                    hours = minutes // 60
                    mins = minutes % 60
                    stats['temps_moyen_resolution'] = f"{hours:02d}:{mins:02d}"
                    
                return stats
            except Exception as e:
                logger.error(f"Erreur lors du calcul des statistiques: {e}")
                return stats

        # Route pour le tableau de bord
        @app.route('/dashboard')
        def dashboard():
            """Page du tableau de bord"""
            if 'user_id' not in session:
                return redirect(url_for('login'))
            stats = get_dashboard_stats()
            tickets_recents = get_ticket_list(limit=5)
            
            # Récupérer les activités récentes
            activites_recentes = get_db("""
                SELECT a.*, u.name as user_name
                FROM activity_logs a
                LEFT JOIN USEUR u ON a.user_id = u.ID
                ORDER BY a.timestamp DESC
                LIMIT 5
            """) or []
            
            return render_template('dashboard.html',
                             stats=stats,
                             tickets_recents=tickets_recents,
                             activites_recentes=activites_recentes)
        
        @app.route('/logout')
        def logout():
            session.clear()
            flash('Déconnexion réussie', 'info')
            return redirect(url_for('login'))
        
        # Routes pour l'inscription (si elles n'existent pas dans les blueprints)
        @app.route('/register', methods=['GET', 'POST'])
        def register():
            logger.debug("Route /register appelée")
            
            if request.method == 'POST':
                logger.debug("Méthode POST détectée pour l'inscription")
                name = request.form.get('name')
                email = request.form.get('email')
                password = request.form.get('password')
                tel = request.form.get('tel')
                age = request.form.get('age')
                confirm_password = request.form.get('password_confirm')
                if password == confirm_password:
                    try:
                        debug_user_id = auth.register_user(name, age, tel, email, password, role='user')
                        flash("Inscription réussie, vous pouvez maintenant vous connecter", "success")
                        logger.info(f"Inscription réussie pour {email} avec ID {debug_user_id}")
                        return redirect(url_for('login'))
                    except Exception as e:
                        logger.error(f"Erreur lors de l'inscription: {e}")
                        flash("Erreur lors de l'inscription : \n" + str(e), "error")
                        return render_template('register.html')
                else:
                    flash("Les mots de passe ne correspondent pas", "error")
                    logger.warning("Tentative d'inscription avec des mots de passe non correspondants")
                    return render_template('register.html')
            logger.debug("Rendu du template register.html")
            return render_template('register.html')
          # Routes pour le profil utilisateur
        @app.route('/profile')
        def profile():
            """Affiche le profil de l'utilisateur connecté"""
            if 'user_id' not in session:
                flash('Vous devez être connecté pour accéder à votre profil', 'error')
                logger.warning("Tentative d'accès au profil sans utilisateur connecté")
                return redirect(url_for('dashboard'))

            try:
                # Essayer d'importer la fonction get_user_info
                try:
                    from onekey.user import get_user_info
                    user_info = get_user_info(session['user_id'])
                except ImportError:
                    # Si le module n'existe pas, créer des données par défaut
                    logger.warning("Module onekey.user non disponible, utilisation de données par défaut")
                    user_info = {
                        'id': session['user_id'],
                        'name': session.get('username', 'Utilisateur'),
                        'email': session.get('user_id', 'admin@example.com'),
                        'age': None,
                        'tel': None,
                        'role': session.get('role', 'user'),
                        'created_at': datetime.now().strftime('%Y-%m-%d'),
                        'is_complete': False  # Indique que le profil n'est pas complet
                    }
                  # Vérifier si user_info est None ou vide
                if not user_info:
                    logger.warning(f"Aucune information utilisateur trouvée pour {session['user_id']}")
                    # Créer un profil par défaut au lieu de déconnecter
                    user_info = {
                        'id': session['user_id'],
                        'name': session.get('username', 'Utilisateur'),
                        'email': session.get('user_email', session.get('user_id', 'admin@example.com')),
                        'age': session.get('user_age'),
                        'tel': session.get('user_tel'),
                        'role': session.get('role', 'user'),
                        'created_at': datetime.now().strftime('%Y-%m-%d'),
                        'is_complete': session.get('profile_complete', False)
                    }
                    
                    # Si le profil n'est pas marqué comme complet, afficher le message
                    if not session.get('profile_complete', False):
                        flash('Profil incomplet, veuillez compléter vos informations', 'warning')
                else:
                    # Mettre à jour avec les données de session si elles existent
                    if session.get('username'):
                        user_info['name'] = session.get('username')
                    if session.get('user_email'):
                        user_info['email'] = session.get('user_email')
                    if session.get('user_age'):
                        user_info['age'] = session.get('user_age')
                    if session.get('user_tel'):
                        user_info['tel'] = session.get('user_tel')
                    
                    user_info['is_complete'] = session.get('profile_complete', user_info.get('is_complete', False))
                
                return render_template('profile.html', user_info=user_info)
                
            except Exception as e:
                logger.error(f"Erreur lors du chargement du profil: {e}")
                flash('Erreur lors du chargement du profil', 'error')
                return redirect(url_for('dashboard'))

        @app.route('/edit_profile', methods=['GET', 'POST'])
        def edit_profile():
            """Permet à l'utilisateur de modifier son profil"""
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            try:
                # Essayer d'importer et d'utiliser le module user
                try:
                    from onekey.user import get_user_info, update_user_info
                    user_info = get_user_info(session['user_id'])
                except ImportError:
                    # Module non disponible, créer des données par défaut
                    logger.warning("Module onekey.user non disponible pour edit_profile")
                    user_info = {
                        'id': session['user_id'],
                        'name': session.get('username', 'Utilisateur'),
                        'email': session.get('user_id', 'admin@example.com'),
                        'age': None,
                        'tel': None,
                        'role': session.get('role', 'user'),
                        'created_at': datetime.now().strftime('%Y-%m-%d'),
                        'is_complete': False                    }
                    flash('Fonction de modification du profil non disponible', 'warning')
                    return render_template('edit_profile.html', user_info=user_info)
                
                if not user_info:
                    # Créer un profil par défaut avec les données de session
                    user_info = {
                        'id': session['user_id'],
                        'name': session.get('username', 'Utilisateur'),
                        'email': session.get('user_email', session.get('user_id', 'admin@example.com')),
                        'age': session.get('user_age'),
                        'tel': session.get('user_tel'),
                        'role': session.get('role', 'user'),
                        'created_at': datetime.now().strftime('%Y-%m-%d'),
                        'is_complete': session.get('profile_complete', False)
                    }
                
                if request.method == 'POST':
                    # Récupérer les données du formulaire
                    name = request.form.get('name')
                    age = request.form.get('age')
                    tel = request.form.get('tel')
                    email = request.form.get('email')
                    
                    # Validation de base
                    if not name or not email:
                        flash('Le nom et l\'email sont obligatoires', 'error')
                        return render_template('edit_profile.html', user_info=user_info)
                    
                    # Mettre à jour les informations en session
                    session['username'] = name
                    session['user_email'] = email
                    session['user_age'] = age if age else None
                    session['user_tel'] = tel if tel else None
                    session['profile_complete'] = True  # Marquer le profil comme complet
                    
                    flash('Profil mis à jour avec succès', 'success')
                    return redirect(url_for('profile'))
                
                return render_template('edit_profile.html', user_info=user_info)
                
            except Exception as e:
                logger.error(f"Erreur lors de la modification du profil: {e}")
                flash('Erreur lors de la modification du profil', 'error')
                return redirect(url_for('profile'))
        
        @app.route('/change_password', methods=['GET', 'POST'])
        def change_password():
            """Permet à l'utilisateur de changer son mot de passe"""
            if 'user_id' not in session:
                return redirect(url_for('login'))
            
            if request.method == 'POST':
                current_password = request.form.get('current_password')
                new_password = request.form.get('new_password')
                confirm_password = request.form.get('confirm_password')
                
                if not current_password or not new_password or not confirm_password:
                    flash('Tous les champs sont obligatoires', 'error')
                    return render_template('change_password.html')
                
                if new_password != confirm_password:
                    flash('Les nouveaux mots de passe ne correspondent pas', 'error')
                    return render_template('change_password.html')
                
                try:
                    from onekey.user import change_password as change_user_password
                    
                    if change_user_password(session['user_id'], current_password, new_password):
                        flash('Mot de passe modifié avec succès', 'success')
                        return redirect(url_for('profile'))
                    else:
                        flash('Erreur lors du changement de mot de passe', 'error')
                        
                except ValueError as e:
                    flash(str(e), 'error')
                except Exception as e:
                    logger.error(f"Erreur lors du changement de mot de passe: {e}")
                    flash('Erreur lors du changement de mot de passe', 'error')
            
            return render_template('change_password.html')        # Import et enregistrement des blueprints
        blueprints_config = [
            {'module': 'routes.tickets', 'bp_name': 'tickets_bp', 'name': 'tickets'},
            {'module': 'routes.inventory', 'bp_name': 'inventory_bp', 'name': 'inventory'},
            {'module': 'activity_screening.routes', 'bp_name': 'activity_bp', 'name': 'activity_screening'},
            {'module': 'routes.admin', 'bp_name': 'admin_bp', 'name': 'admin'},
            {'module': 'routes.main', 'bp_name': 'main_bp', 'name': 'main'}
        ]        
        
        blueprints_imported = []

        # Modification de la fonction register_blueprints pour éviter l'utilisation de 'flash' en dehors du contexte de requête
        def register_blueprints(app):
            for bp_config in blueprints_config:
                try:
                    module = __import__(bp_config['module'], fromlist=[bp_config['bp_name']])
                    blueprint = getattr(module, bp_config['bp_name'])
                    app.register_blueprint(blueprint)
                    blueprints_imported.append(bp_config['name'])
                    logger.info(f"Blueprint {bp_config['name']} enregistré")
                    logger.info(f"Blueprints enregistrés: {', '.join(blueprints_imported)}")
                except (ImportError, AttributeError) as e:
                    logger.warning(f"Blueprint {bp_config['name']} non disponible: {e}")
                    # Activer le mode SOS si un blueprint n'est pas chargé
                    StartSOSMode(app)
                    with app.app_context():  # Ajout d'un contexte d'application pour utiliser 'flash'
                        flash(f"Le module {bp_config['name']} n'est pas disponible, certaines fonctionnalités peuvent être limitées.", "warning")

        register_blueprints(app)
        
        if not blueprints_imported:
            logger.warning("Aucun blueprint enregistré, seules les routes de base sont disponibles")
            StartSOSMode(app)
            
        
        # Gestionnaires d'erreur
        @app.errorhandler(500)
        def internal_error(error):
            logger.error(f"Erreur interne: {error}")
            return render_template('errors/500.html'), 500
        
        @app.errorhandler(404)
        def not_found(error):
            logger.warning(f"Page non trouvée: {request.url}")
            return render_template('errors/404.html'), 404
        
        @app.route('/favicon.ico')
        def favicon():
            """Route pour servir le favicon"""
            return send_from_directory('static/images', 'favicon.ico')
        
        @app.route('/robots.txt')
        def robots():
            """Route pour servir le fichier robots.txt"""
            return send_from_directory('static', 'robots.txt'), 200
        return app
        
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation de l'application: {e}")
        raise

def run_main_server(queue):
    """Serveur principal"""
    try:
        app = create_app()
        logger.info("=== DÉMARRAGE DU SERVEUR PRINCIPAL ===")
        app.run(host='127.0.0.1', port=5000)
    except Exception as e:
        logger.error(f"Erreur serveur principal: {e}")
        queue.put(('error', str(e)))

def run_backup_server(queue):
    """Serveur de secours pour les pages essentielles"""
    try:
        backup_app = Flask('backup')
        backup_app.config['SOS_MODE'] = True
        
        @backup_app.route('/waiting')
        def waiting():
            return render_template('waiting.html')
            
        @backup_app.route('/health')
        def health():
            return state_handler.get_health_status()
            
        logger.info("=== DÉMARRAGE DU SERVEUR DE SECOURS ===")
        backup_app.run(host='127.0.0.1', port=5001)
    except Exception as e:
        logger.error(f"Erreur serveur secours: {e}")
        queue.put(('backup_error', str(e)))

def start_servers():
    """Démarre les serveurs avec surveillance"""
    main_process = Process(target=run_main_server, args=(process_queue,))
    backup_process = Process(target=run_backup_server, args=(process_queue,))
    
    main_process.start()
    backup_process.start()
    
    try:
        while True:
            if not process_queue.empty():
                msg_type, msg = process_queue.get()
                if msg_type == 'error':
                    logger.critical(f"Erreur serveur principal: {msg}")
                    state_handler.set_sos_mode(True)
                elif msg_type == 'backup_error':
                    logger.critical(f"Erreur serveur secours: {msg}")
            
            if not main_process.is_alive():
                logger.warning("Redémarrage du serveur principal...")
                main_process = Process(target=run_main_server, args=(process_queue,))
                main_process.start()
    except KeyboardInterrupt:
        logger.info("Arrêt des serveurs demandé...")
        main_process.terminate()
        backup_process.terminate()
        main_process.join()
        backup_process.join()

if __name__ == '__main__':
    freeze_support()
    try:
        start_servers()
    except Exception as e:
        logger.critical(f"Erreur fatale: {e}")
        sys.exit(1)