from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import traceback
import sys
import json
import sqlite3
import logging
from logging.handlers import RotatingFileHandler
from datetime import timedelta, datetime
from utils.db_manager import init_db_manager, db_manager, get_db

# Configuration des logs
if not os.path.exists('logs'):
    os.makedirs('logs')

log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler = RotatingFileHandler('logs/glpibis.log', maxBytes=1024*1024, backupCount=5)
handler.setFormatter(log_formatter)
handler.setLevel(logging.DEBUG)

# Configuration du logger de l'application
app_logger = logging.getLogger('glpibis')
app_logger.setLevel(logging.DEBUG)
app_logger.addHandler(handler)

# S'assurer que la base de données est initialisée dès le démarrage
def init_db():
    """Initialise la base de données et retourne le gestionnaire"""
    # Lire la configuration
    try:
        with open('config/conf.conf', 'r') as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        config = {"db_type": "sqlite"}
    
    db_type = config.get('db_type', 'sqlite')
    mysql_params = config.get('mysql', {}) if db_type == 'mysql' else None
    
    return init_db_manager(db_type, mysql_params)

db_manager_instance = init_db()
# Note: Cette initialisation doit être effectuée avant toute importation de modules qui utilisent la base de données
from onekey.auth import register_user, login_user, validate_session, logout_user, validate_password
from tickets.routes import tickets_bp
from inventory.routes import inventory_bp
from activity_screening.routes import activity_bp
from admin.routes import admin_bp

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Génération d'une clé secrète aléatoire
app.permanent_session_lifetime = timedelta(hours=8)  # Session de 8 heures
app.config['SOS_MODE'] = False  # Par défaut, le mode SOS est désactivé
app.config['SOS_ERROR'] = None  # Message d'erreur en mode SOS
app.config['SOS_TRACEBACK'] = None  # Traceback de l'erreur en mode SOS

# Vérification du premier lancement
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', 'conf.conf')
def is_first_launch():
    if not os.path.exists(CONFIG_FILE):
        return True
    # Vérifier que le fichier est également accessible en lecture
    try:
        with open(CONFIG_FILE, 'r') as f:
            json.load(f)
        return False
    except (IOError, json.JSONDecodeError):
        # Si le fichier existe mais n'est pas accessible ou mal formaté
        return True

def save_config(config):
    # Assurez-vous que le répertoire existe
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def create_default_config():
    """Crée un fichier de configuration par défaut en cas de problème."""
    default_config = {
        "db_type": "sqlite",
        "company_name": "GLPIbis",
        "app_settings": {
            "session_duration_hours": 24,
            "debug_mode": True,
            "log_level": "INFO"
        },
        "modules": {
            "tickets": {
                "enabled": True,
                "auto_close_days": 30,
                "notification_enabled": True
            },
            "inventory": {
                "enabled": True,
                "qr_code_enabled": True
            },
            "activity_screening": {
                "enabled": True,
                "refresh_interval_seconds": 5
            }
        }
    }
    
    # Assurez-vous que le répertoire existe
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    
    # Écrire la configuration
    with open(CONFIG_FILE, 'w') as f:
        json.dump(default_config, f, indent=4)
    
    return default_config

# Enregistrement des blueprints
app.register_blueprint(tickets_bp, url_prefix='/tickets')
app.register_blueprint(inventory_bp, url_prefix='/inventory')
app.register_blueprint(activity_bp, url_prefix='/activity')
app.register_blueprint(admin_bp, url_prefix='/admin')

# Gestionnaire d'erreurs général pour le mode SOS
@app.errorhandler(500)
def server_error(e):
    app.config['SOS_MODE'] = True
    error_tb = traceback.format_exc()
    error_type = sys.exc_info()[0].__name__ if sys.exc_info()[0] else "Unknown Error"
    app.config['SOS_ERROR'] = str(e)
    app.config['SOS_TRACEBACK'] = error_tb
    
    # Collecter des informations supplémentaires pour le diagnostic
    diagnostic_info = {
        "python_version": sys.version,
        "os": os.name,
        "flask_version": Flask.__version__,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "endpoint": request.endpoint if request else None,
        "route": request.path if request else None,
        "method": request.method if request else None,
    }
    
    # Tester la configuration si disponible
    config_status = "Non testé"
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                json.load(f)
                config_status = "Valide"
        else:
            config_status = "Fichier manquant"
    except Exception as config_err:
        config_status = f"Invalide: {str(config_err)}"
    
    diagnostic_info["config_status"] = config_status
    
    # Tester l'accès à la base de données
    db_status = "Non testé"
    try:
        from utils.db_manager import DBManager
        db_manager = DBManager()
        success, message = db_manager.test_connection()
        db_status = f"{'OK' if success else 'Erreur'}: {message}"
    except Exception as db_err:
        db_status = f"Erreur: {str(db_err)}"
    
    diagnostic_info["db_status"] = db_status
    
    app.config['SOS_DIAGNOSTIC'] = diagnostic_info
    
    return render_template('sos.html', 
                          error_type=error_type,
                          error=str(e),
                          traceback=error_tb,
                          diagnostic=diagnostic_info), 500

# Gestionnaire d'erreur pour les exceptions de base de données
@app.errorhandler(Exception)
def handle_exception(e):
    if "database" in str(e).lower() or "db" in str(e).lower() or "sql" in str(e).lower():
        app.logger.error(f"Erreur de base de données: {str(e)}")
        app.config['SOS_MODE'] = True
        error_tb = traceback.format_exc()
        app.config['SOS_ERROR'] = str(e)
        app.config['SOS_TRACEBACK'] = error_tb
        return render_template('sos.html', 
                              error_type="Erreur de Base de Données",
                              error=str(e),
                              traceback=error_tb), 500
    # Pour les autres erreurs, propager l'exception pour que Flask puisse la gérer
    return app.handle_exception(e)

# Rendre get_db et now disponibles dans tous les templates
@app.context_processor
def utility_processor():
    from datetime import datetime
    return dict(
        get_db=get_db, 
        now=datetime.now(), 
        SOS_MODE=app.config.get('SOS_MODE', False),
        SOS_ERROR=app.config.get('SOS_ERROR')
    )

# Configuration de la session
@app.before_request
def make_session_permanent():
    session.permanent = True

# Middleware pour vérifier l'authentification
@app.before_request
def check_auth():
    # Routes publiques qui ne nécessitent pas d'authentification
    public_routes = ['index', 'login', 'register', 'static', 'check_session', 'test_sos', 'server_error', 'handle_exception', 'setup']
    if request.endpoint in public_routes or request.path.startswith('/static/'):
        return

    user_id = session.get('user_id')
    token = session.get('token')
    
    print(f"DEBUG - check_auth: Vérification de l'authentification - endpoint: {request.endpoint}, user_id: {user_id}, token: {token[:5] if token else None}...")

    # S'il n'y a pas de session, rediriger vers la page de connexion
    if not user_id or not token:
        print("DEBUG - check_auth: Pas de session active, redirection vers login")
        session.clear()
        flash("Votre session a expiré ou vous n'êtes pas connecté. Veuillez vous reconnecter.", "warning")
        return redirect(url_for('login'))

    try:
        # Valider la session avec la base de données
        is_valid = validate_session(token)
        print(f"DEBUG - check_auth: Résultat de validate_session: {is_valid}")
        
        if not is_valid:
            # Session invalide ou expirée selon la base de données
            print("DEBUG - check_auth: Session invalide ou expirée selon la base de données")
            session.clear()
            flash("Votre session a expiré. Veuillez vous reconnecter.", "warning")
            return redirect(url_for('login'))
        
        # Si le token est valide, prolonger la session dans la base de données
        from utils.db_manager import load_config
        config = load_config()
        session_duration_hours = config.get('app_settings', {}).get('session_duration_hours', 24)
        
        # Mise à jour de la date d'expiration de la session
        try:
            expiry_date = (datetime.now() + timedelta(hours=session_duration_hours)).strftime("%Y-%m-%d %H:%M:%S")
            get_db("UPDATE sessions SET expiry_date = ? WHERE token = ?", (expiry_date, token))
            print(f"DEBUG - check_auth: Session prolongée jusqu'à {expiry_date}")
        except Exception as e:
            # En cas d'erreur lors de la prolongation, on ignore et continue
            print(f"DEBUG - check_auth: Erreur lors de la prolongation de la session: {str(e)}")
            app.logger.warning(f"Erreur lors de la prolongation de la session: {str(e)}")
    except Exception as e:
        print(f"DEBUG - check_auth: Erreur lors de la vérification de la session: {str(e)}")
        app.logger.error(f"Erreur lors de la vérification de la session: {str(e)}")
        # En cas d'erreur grave, déconnexion par sécurité
        session.clear()
        flash("Une erreur s'est produite avec votre session. Veuillez vous reconnecter.", "warning")
        return redirect(url_for('login'))

    # Marquer la session comme modifiée pour qu'elle soit sauvegardée
    session.modified = True
    print("DEBUG - check_auth: Session validée avec succès")

@app.before_request
def check_first_launch():
    if is_first_launch() and request.endpoint != 'setup':
        return redirect(url_for('setup'))

@app.route('/')
def index():
    from datetime import datetime
    return render_template('index.html', now=datetime.now())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash("Veuillez remplir tous les champs", "error")
            return render_template('login.html')

        try:
            app.logger.info(f"Tentative de connexion pour l'email : {email}")
            result = login_user(email, password)
            if result['status'] == 'success':
                session['user_id'] = result['user_id']
                session['username'] = result['username']
                session['token'] = result['token']
                session['role'] = result.get('role', 'user')
                session.permanent = True
                flash("Connexion réussie !", "success")
                app.logger.info(f"Connexion réussie pour {email}")
                return redirect(url_for('dashboard'))
            else:
                flash(result['message'], "error")
                app.logger.warning(f"Échec de connexion pour {email}: {result['message']}")
        except Exception as e:
            app.logger.error(f"Erreur lors de la connexion pour {email}: {str(e)}")
            flash(f"Erreur de connexion: {str(e)}", "error")

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        age = request.form.get('age')
        tel = request.form.get('tel')
        email = request.form.get('email')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')

        if not all([name, age, tel, email, password, password_confirm]):
            flash("Veuillez remplir tous les champs", "error")
            return render_template('register.html')

        if password != password_confirm:
            flash("Les mots de passe ne correspondent pas", "error")
            return render_template('register.html')

        try:
            user_id = register_user(name, age, tel, email, password)
            if user_id:
                flash("Compte créé avec succès! Vous pouvez maintenant vous connecter.", "success")
                return redirect(url_for('login'))
            else:
                flash("Une erreur s'est produite lors de la création du compte", "error")
        except ValueError as e:
            flash(str(e), "error")
        except Exception as e:
            flash(f"Erreur d'inscription: {str(e)}", "error")

    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    stats = {}
    tickets_ouverts = get_db("""
        SELECT COUNT(*) as total,
        SUM(CASE WHEN gravite >= 8 THEN 1 ELSE 0 END) as urgents
        FROM tiqué WHERE open = 1
    """)
    stats['tickets_ouverts'] = tickets_ouverts[0][0] if tickets_ouverts else 0
    stats['tickets_urgents'] = tickets_ouverts[0][1] if tickets_ouverts else 0

    stats['tickets_resolus'] = get_db("""
        SELECT COUNT(*) FROM tiqué 
        WHERE open = 0
    """)[0][0]

    stats['tickets_en_attente'] = get_db("""
        SELECT COUNT(*) FROM tiqué 
        WHERE open = 1 AND tag = 'en_attente'
    """)[0][0]

    # Vérifier si la colonne date_close existe
    try:
        temps_moyen = get_db("""
            SELECT AVG((julianday(date_close) - julianday(date_open)) * 24)
            FROM tiqué 
            WHERE open = 0 
            AND date_close IS NOT NULL
        """)
    except sqlite3.OperationalError:
        # Si la colonne n'existe pas, définir le temps moyen comme None
        temps_moyen = [(None,)]
        # Ajouter la colonne si elle n'existe pas
        try:
            get_db("ALTER TABLE tiqué ADD COLUMN date_close TIMESTAMP")
            print("Colonne 'date_close' ajoutée à la table tiqué")
        except Exception as e:
            print(f"Impossible d'ajouter la colonne date_close: {str(e)}")
    avg_hours = temps_moyen[0][0] if temps_moyen and temps_moyen[0][0] else 0
    stats['temps_moyen_resolution'] = f"{int(avg_hours)}h" if avg_hours else "N/A"

    tickets_recents = get_db("""
        SELECT t.ID_tiqué, t.titre, t.gravite, t.open, t.tag,
               u.name as assigne_a, t.date_open
        FROM tiqué t
        LEFT JOIN USEUR u ON t.ID_user = u.ID
        ORDER BY t.date_open DESC
        LIMIT 10
    """)

    tickets_formated = []
    for t in tickets_recents:
        priorite_class = {
            9: 'danger',
            8: 'danger',
            7: 'warning',
            6: 'warning',
            5: 'info',
        }.get(t[2], 'secondary')

        statut_class = 'success' if not t[3] else 'warning' if t[4] == 'en_attente' else 'primary'

        tickets_formated.append({
            'id': t[0],
            'titre': t[1],
            'priorite': t[2],
            'priorite_class': priorite_class,
            'statut': 'Fermé' if not t[3] else 'En attente' if t[4] == 'en_attente' else 'Ouvert',
            'statut_class': statut_class,
            'assigne_a': t[5],
            'derniere_maj': t[6]
        })

    activites_recentes = get_db("""
        SELECT al.timestamp, u.name, al.description
        FROM activity_logs al
        LEFT JOIN USEUR u ON al.user_id = u.ID
        ORDER BY al.timestamp DESC
        LIMIT 15
    """)

    activities_formatted = [{
        'timestamp': a[0],
        'user': a[1],
        'description': a[2]
    } for a in activites_recentes]

    return render_template('dashboard.html',
                         stats=stats,
                         tickets_recents=tickets_formated,
                         activites_recentes=activities_formatted)

@app.route('/logout')
def logout():
    token = session.get('token')
    if token:
        try:
            logout_user(token)
        except Exception as e:
            pass

    session.clear()
    flash("Vous avez été déconnecté avec succès", "success")
    return redirect(url_for('index'))

@app.route('/check-session')
def check_session():
    if 'user_id' in session and 'token' in session:
        return json.dumps({
            'status': 'logged_in',
            'user_id': session['user_id'],
            'username': session.get('username', 'Utilisateur')
        })
    else:
        return json.dumps({'status': 'logged_out'})

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    # Importer validate_password dès le début de la fonction
    from onekey.auth import validate_password
    
    if not is_first_launch():
        return redirect(url_for('index'))

    if request.method == 'POST':
        db_type = request.form.get('db_type')
        admin_name = request.form.get('admin_name')
        admin_email = request.form.get('admin_email')
        admin_password = request.form.get('admin_password')
        admin_password_confirm = request.form.get('admin_password_confirm')
        company_name = request.form.get('company_name', 'Mon Entreprise')

        # Validation du formulaire
        errors = []
        if not db_type:
            errors.append("Le type de base de données est requis")
        
        if not admin_name or len(admin_name) < 2:
            errors.append("Le nom d'administrateur est requis (minimum 2 caractères)")
            
        if not admin_email or '@' not in admin_email:
            errors.append("Une adresse email valide est requise")
            
        if not admin_password:
            errors.append("Le mot de passe administrateur est requis")
        elif not validate_password(admin_password):
            errors.append("Le mot de passe doit contenir au moins 8 caractères, une majuscule, une minuscule, un chiffre et un caractère spécial")
            
        if admin_password != admin_password_confirm:
            errors.append("Les mots de passe ne correspondent pas")
            
        # Validation spécifique pour MySQL
        if db_type == 'mysql':
            mysql_host = request.form.get('mysql_host')
            mysql_port = request.form.get('mysql_port', '3306')
            mysql_db = request.form.get('mysql_db')
            mysql_user = request.form.get('mysql_user')
            
            if not mysql_host:
                errors.append("L'hôte MySQL est requis")
            if not mysql_db:
                errors.append("Le nom de la base de données MySQL est requis")
            if not mysql_user:
                errors.append("L'utilisateur MySQL est requis")
                
        if errors:
            for error in errors:
                flash(error, "error")
            return render_template('setup.html')

        try:
            # Créer le dossier de configuration s'il n'existe pas
            os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
            
            # Récupérer les paramètres MySQL si nécessaire
            mysql_params = {}
            if db_type == 'mysql':
                mysql_host = request.form.get('mysql_host')
                mysql_port = request.form.get('mysql_port', '3306')
                mysql_db = request.form.get('mysql_db')
                mysql_user = request.form.get('mysql_user')
                mysql_password = request.form.get('mysql_password', '')
                
                mysql_params = {
                    'host': mysql_host,
                    'port': mysql_port,
                    'db': mysql_db,
                    'user': mysql_user,
                    'password': mysql_password
                }
            
            # Sauvegarder la configuration
            config = {
                'db_type': db_type,
                'company_name': company_name,
                'admin': {
                    'name': admin_name,
                    'email': admin_email
                },
                'app_settings': {
                    'session_duration_hours': 24,
                    'debug_mode': False,
                    'log_level': "INFO"
                },
                'setup_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Ajouter les paramètres MySQL à la configuration si nécessaire
            if db_type == 'mysql':
                config['mysql'] = mysql_params
                
            save_config(config)
            
            # Configurer la base de données
            from utils.db_manager import init_db_manager
            try:
                db_manager_instance = init_db_manager(db_type, mysql_params if db_type == 'mysql' else None)
                db_manager_instance.create_tables()
                db_manager_instance.verify_table_structure()
            except Exception as db_err:
                flash(f"Erreur de connexion à la base de données: {str(db_err)}", "error")
                raise Exception(f"Erreur d'initialisation de la base de données: {str(db_err)}")
            
            # Créer l'utilisateur administrateur
            from onekey.auth import register_user
            # Nous avons déjà validé le mot de passe, inutile de le faire à nouveau
            user_id = register_user(admin_name, 0, '', admin_email, admin_password, role='admin')
            
            if user_id:
                flash(f"Configuration initiale réussie ! L'administrateur {admin_email} a été créé.", "success")
                return redirect(url_for('login'))
            else:
                flash("Erreur lors de la création du compte administrateur", "error")
                # Supprimer le fichier de configuration en cas d'erreur pour permettre une nouvelle tentative
                if os.path.exists(CONFIG_FILE):
                    os.remove(CONFIG_FILE)
        except Exception as e:
            flash(f"Erreur lors de la configuration : {str(e)}", "error")
            app.logger.error(f"Erreur setup: {str(e)}")
            app.logger.error(traceback.format_exc())
            # Supprimer le fichier de configuration en cas d'erreur pour permettre une nouvelle tentative
            if os.path.exists(CONFIG_FILE):
                os.remove(CONFIG_FILE)

    return render_template('setup.html')

# Ajout du gestionnaire d'erreur 404
@app.errorhandler(404)
def not_found(e):
    if request.path.startswith('/tickets/') and '/close' in request.path:
        return redirect(url_for('tickets_bp.tickets_list')), 302
    return render_template('404.html'), 404

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', debug=True)
    except Exception as e:
        if "database" in str(e).lower() or "db" in str(e).lower() or "sql" in str(e).lower():
            app.config['SOS_MODE'] = True
            app.config['SOS_ERROR'] = str(e)
            app.config['SOS_TRACEBACK'] = traceback.format_exc()
            app.run(host='0.0.0.0', debug=True)
        else:
            raise