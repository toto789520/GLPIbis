from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import json
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

# Enregistrement des blueprints
app.register_blueprint(tickets_bp, url_prefix='/tickets')
app.register_blueprint(inventory_bp, url_prefix='/inventory')
app.register_blueprint(activity_bp, url_prefix='/activity')
app.register_blueprint(admin_bp, url_prefix='/admin')

# Rendre get_db disponible dans tous les templates
@app.context_processor
def utility_processor():
    return dict(get_db=get_db)

# Configuration de la session
@app.before_request
def make_session_permanent():
    session.permanent = True

# Middleware pour vérifier l'authentification
@app.before_request
def check_auth():
    # Liste des routes qui ne nécessitent pas d'authentification
    public_routes = ['index', 'login', 'register', 'static', 'check_session']
    
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
    # Vérification explicite de l'authentification pour le dashboard
    user_id = session.get('user_id')
    username = session.get('username')
    token = session.get('token')
    
    print(f"Accès au dashboard - user_id: {user_id}, username: {username}, token présent: {'oui' if token else 'non'}")
    
    # Double vérification pour le dashboard
    if not user_id or not token:
        print("Tentative d'accès au dashboard sans authentification")
        session.clear()
        flash("Veuillez vous connecter pour accéder à votre tableau de bord", "warning")
        return redirect(url_for('login'))
    
    # Créer un objet user pour le template avec toutes les informations nécessaires
    user = {
        'id': user_id,
        'name': username or 'Utilisateur',  # Valeur par défaut si username n'existe pas
        'email': '',
        'role': session.get('role', 'user'),
        'creation_date': '',
        'stats': {
            'tickets_created': 0,
            'tickets_participated': 0,
            'comments': 0
        }
    }
    
    # Récupérer les détails utilisateur depuis la base de données
    try:
        # Récupérer directement la date de création en utilisant le nom de colonne
        date_creation_query = """
            SELECT dete_de_creation 
            FROM USEUR 
            WHERE ID = %s
        """
        creation_date_result = get_db(date_creation_query, (user_id,))
        
        if creation_date_result and len(creation_date_result) > 0 and creation_date_result[0][0]:
            try:
                creation_date = creation_date_result[0][0]
                # Si c'est une chaîne, essayer de la parser
                if isinstance(creation_date, str):
                    # Essayer d'abord le format complet avec heures
                    try:
                        parsed_date = datetime.strptime(creation_date, '%Y-%m-%d %H:%M:%S')
                        user['creation_date'] = parsed_date.strftime('%d/%m/%Y %H:%M')
                    except ValueError:
                        # Essayer juste la date
                        try:
                            parsed_date = datetime.strptime(creation_date, '%Y-%m-%d')
                            user['creation_date'] = parsed_date.strftime('%d/%m/%Y')
                        except ValueError:
                            # Si aucun format ne correspond, utiliser tel quel
                            user['creation_date'] = creation_date
                elif isinstance(creation_date, datetime):
                    # Si c'est déjà un objet datetime
                    user['creation_date'] = creation_date.strftime('%d/%m/%Y %H:%M')
                else:
                    # Autre type, convertir en string
                    user['creation_date'] = str(creation_date)
            except Exception as e:
                print(f"Erreur lors du formatage de la date: {str(e)}")
                user['creation_date'] = str(creation_date_result[0][0])
        
        # Récupérer les autres informations utilisateur
        user_data = get_db("SELECT * FROM USEUR WHERE ID = %s", (user_id,))
        if user_data and len(user_data) > 0:
            user_row = user_data[0]
            col_count = len(user_row)
            
            # Récupérer le nom d'utilisateur
            if col_count > 3:  # Si format est (ID, name, age, tel, ...)
                user['name'] = username or user_row[1]
            elif col_count > 1:  # Si format est (ID, name, ...)
                user['name'] = username or user_row[1]
            
            # Récupérer l'email
            if col_count > 5:  # Si format est (ID, name, age, tel, hashed_password, email, ...)
                user['email'] = user_row[5]
            elif col_count > 2:  # Si format est (ID, name, email, ...)
                user['email'] = user_row[2]
        
        # Récupérer les statistiques de l'utilisateur
        stats_data = get_db("SELECT * FROM state WHERE id_user = %s", (user_id,))
        if stats_data and len(stats_data) > 0:
            stats_row = stats_data[0]
            if len(stats_row) > 1:
                user['stats']['tickets_created'] = stats_row[1] if stats_row[1] is not None else 0
            if len(stats_row) > 2:
                user['stats']['tickets_participated'] = stats_row[2] if stats_row[2] is not None else 0
            if len(stats_row) > 3:
                user['stats']['comments'] = stats_row[3] if stats_row[3] is not None else 0
    
    except Exception as e:
        print(f"Erreur lors de la récupération des données utilisateur: {str(e)}")
        # L'objet user minimal est déjà créé avec des valeurs par défaut
    
    return render_template('dashboard.html', user=user, now=datetime.now())

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

# Point d'entrée principal
if __name__ == '__main__':
    # S'assurer que la base de données est configurée
    set_up_database()
    
    # Démarrer l'application Flask
    app.run(debug=True)