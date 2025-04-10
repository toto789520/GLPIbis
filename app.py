from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import json
import traceback
import sys
from datetime import timedelta, datetime
from setup import set_up_database
from onekey.auth import register_user, login_user, validate_session, logout_user
from tickets.routes import tickets_bp
from inventory.routes import inventory_bp
from activity_screening.routes import activity_bp
from admin.routes import admin_bp
from utils.db import get_db

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Génération d'une clé secrète aléatoire
app.permanent_session_lifetime = timedelta(hours=8)  # Session de 8 heures
app.config['SOS_MODE'] = False  # Par défaut, le mode SOS est désactivé
app.config['SOS_ERROR'] = None  # Message d'erreur en mode SOS
app.config['SOS_TRACEBACK'] = None  # Traceback de l'erreur en mode SOS

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
    return render_template('sos.html', 
                          error_type=error_type,
                          error=str(e),
                          traceback=error_tb), 500

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
    # Liste des routes qui ne nécessitent pas d'authentification
    public_routes = ['index', 'login', 'register', 'static', 'check_session', 'test_sos', 'server_error', 'handle_exception']
    
    # Si la route actuelle ne nécessite pas d'authentification, on passe
    if request.endpoint in public_routes or request.path.startswith('/static/'):
        return
    
    # Vérification de la session
    user_id = session.get('user_id')
    token = session.get('token')
    
    print(f"Vérification d'authentification pour {request.endpoint}: user_id={user_id}, token présent: {'oui' if token else 'non'}")
    
    # Vérification stricte de l'authentification
    if not user_id or not token:
        print(f"Session incomplète: user_id={user_id}, token présent: {'oui' if token else 'non'}")
        session.clear()  # On efface complètement la session invalide
        flash("Votre session a expiré ou vous n'êtes pas connecté. Veuillez vous reconnecter.", "warning")
        return redirect(url_for('login'))
        
    # Vérifier si la session est valide
    try:
        is_valid = validate_session(token)
        if not is_valid:
            print(f"Session invalide pour l'utilisateur {user_id}")
            session.clear()
            flash("Votre session a expiré. Veuillez vous reconnecter.", "warning")
            return redirect(url_for('login'))
    except Exception as e:
        print(f"Erreur dans la validation de session: {str(e)}")
        # En cas d'erreur de validation, on demande quand même à l'utilisateur de se reconnecter
        session.clear()
        flash("Une erreur s'est produite avec votre session. Veuillez vous reconnecter.", "warning")
        return redirect(url_for('login'))
    
    # Prolonger la durée de la session à chaque requête
    session.modified = True

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
            result = login_user(email, password)
            if result['status'] == 'success':
                # Stocker les infos utilisateur dans la session
                session['user_id'] = result['user_id']
                session['username'] = result['username']
                session['token'] = result['token']
                session['role'] = result.get('role', 'user')
                session.permanent = True
                
                # Redirection vers le tableau de bord
                flash("Connexion réussie !", "success")
                return redirect(url_for('dashboard'))
            else:
                flash(result['message'], "error")
        except Exception as e:
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
    """Page du tableau de bord principal"""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Statistiques des tickets
    stats = {}
    
    # Tickets ouverts et urgents
    tickets_ouverts = get_db("""
        SELECT COUNT(*) as total,
        SUM(CASE WHEN gravite >= 8 THEN 1 ELSE 0 END) as urgents
        FROM tiqué WHERE open = 1
    """)
    stats['tickets_ouverts'] = tickets_ouverts[0][0] if tickets_ouverts else 0
    stats['tickets_urgents'] = tickets_ouverts[0][1] if tickets_ouverts else 0
    
    # Tickets résolus cette semaine
    stats['tickets_resolus'] = get_db("""
        SELECT COUNT(*) FROM tiqué 
        WHERE open = 0 
        AND date_close >= DATE_SUB(NOW(), INTERVAL 7 DAY)
    """)[0][0]
    
    # Tickets en attente
    stats['tickets_en_attente'] = get_db("""
        SELECT COUNT(*) FROM tiqué 
        WHERE open = 1 AND tag = 'en_attente'
    """)[0][0]
    
    # Temps moyen de résolution
    temps_moyen = get_db("""
        SELECT AVG(TIMESTAMPDIFF(HOUR, date_open, date_close))
        FROM tiqué 
        WHERE open = 0 
        AND date_close IS NOT NULL
    """)
    avg_hours = temps_moyen[0][0] if temps_moyen and temps_moyen[0][0] else 0
    stats['temps_moyen_resolution'] = f"{int(avg_hours)}h" if avg_hours else "N/A"
    
    # Tickets récents
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
    
    # Activités récentes
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
    print(f"Déconnexion demandée - token présent: {'oui' if token else 'non'}")
    
    if token:
        try:
            logout_user(token)
        except Exception as e:
            print(f"Erreur lors de la déconnexion: {str(e)}")
    
    # Vider la session dans tous les cas
    session.clear()
    flash("Vous avez été déconnecté avec succès", "success")
    return redirect(url_for('index'))

# Route pour tester l'état de la session
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

# Route pour tester le mode SOS
@app.route('/test-sos')
def test_sos():
    # Accessible sans authentification
    # Seulement accessible en mode debug
    if app.debug:
        raise Exception("Ceci est un test du mode SOS")
    return "Mode SOS test non disponible en production"

# Point d'entrée principal
if __name__ == '__main__':
    try:
        # S'assurer que la base de données est configurée
        set_up_database()
        
        # Démarrer l'application Flask
        app.run(host='0.0.0.0', debug=True)
    except Exception as e:
        print(f"ERREUR CRITIQUE AU DÉMARRAGE: {str(e)}")
        
        # Démarrer l'application en mode SOS si l'erreur est liée à la base de données
        if "database" in str(e).lower() or "db" in str(e).lower() or "sql" in str(e).lower():
            print("Démarrage en MODE SOS...")
            app.config['SOS_MODE'] = True
            app.config['SOS_ERROR'] = str(e)
            app.config['SOS_TRACEBACK'] = traceback.format_exc()
            app.run(host='0.0.0.0', debug=True)
        else:
            # Pour les autres erreurs critiques, interrompre le démarrage
            raise