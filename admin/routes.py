from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from utils.db import get_db, log_activity
from datetime import datetime
import json
import hashlib

# Création du Blueprint pour les routes liées à l'administration
admin_bp = Blueprint('admin', __name__, template_folder='templates')

@admin_bp.before_request
def check_admin():
    """Vérifie que l'utilisateur est un admin avant d'accéder aux routes d'administration"""
    if session.get('role') != 'admin':
        flash("Vous n'avez pas les permissions nécessaires pour accéder à cette page.", "error")
        return redirect(url_for('index'))

@admin_bp.route('/')
def index():
    """Page d'accueil de l'administration"""
    return render_template('admin/index.html', now=datetime.now())

@admin_bp.route('/users')
def users():
    """Gestion des utilisateurs"""
    users = get_db("SELECT * FROM USEUR")
    return render_template('admin/users.html', users=users, now=datetime.now())

@admin_bp.route('/users/<user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    """Édition des informations et permissions d'un utilisateur"""
    if request.method == 'POST':
        # Récupérer les données du formulaire
        name = request.form.get('name')
        email = request.form.get('email')
        role = request.form.get('role')
        permissions = request.form.getlist('permissions')
        
        # Enregistrer les permissions dans un format JSON
        permissions_json = json.dumps(permissions)
        
        # Mettre à jour les informations de l'utilisateur
        try:
            # S'assurer que la colonne role existe
            columns = get_db("SHOW COLUMNS FROM USEUR LIKE 'role'")
            if not columns:
                get_db("ALTER TABLE USEUR ADD COLUMN role VARCHAR(20) DEFAULT 'user'")
                
            # Mettre à jour les informations de l'utilisateur
            get_db("UPDATE USEUR SET name = %s, email = %s, role = %s WHERE ID = %s", 
                  (name, email, role, user_id))
            
            # Création de la table user_permissions si elle n'existe pas
            get_db("""
                CREATE TABLE IF NOT EXISTS user_permissions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id VARCHAR(255) NOT NULL,
                    permissions TEXT NOT NULL,
                    UNIQUE KEY unique_user (user_id)
                )
            """)
            
            # Vérifier si une entrée de permission existe déjà pour cet utilisateur
            existing_perm = get_db("SELECT * FROM user_permissions WHERE user_id = %s", (user_id,))
            
            if existing_perm:
                # Mettre à jour les permissions existantes
                get_db("UPDATE user_permissions SET permissions = %s WHERE user_id = %s", 
                      (permissions_json, user_id))
            else:
                # Créer une nouvelle entrée de permissions
                get_db("INSERT INTO user_permissions (user_id, permissions) VALUES (%s, %s)", 
                      (user_id, permissions_json))
            
            log_activity(session.get('user_id'), 'update', 'user', f"Mise à jour des informations de l'utilisateur {user_id}")
            flash("Informations de l'utilisateur mises à jour avec succès", "success")
            
        except Exception as e:
            flash(f"Erreur lors de la mise à jour: {str(e)}", "error")
        
        return redirect(url_for('admin.users'))
    
    # Méthode GET: Récupérer les informations de l'utilisateur pour affichage
    user_data = get_db("SELECT * FROM USEUR WHERE ID = %s", (user_id,))
    
    if not user_data:
        flash("Utilisateur non trouvé", "error")
        return redirect(url_for('admin.users'))
        
    user = user_data[0]
    
    # Convertir l'utilisateur en dictionnaire pour faciliter l'accès
    user_dict = {
        'id': user[0],
        'name': user[3] if len(user) > 3 else '',
        'email': user[2] if len(user) > 2 else '',
        'role': user[-1] if len(user) > 5 else 'user'  # On suppose que le rôle est la dernière colonne
    }
    
    # Récupérer les permissions actuelles de l'utilisateur
    try:
        perms_data = get_db("SELECT permissions FROM user_permissions WHERE user_id = %s", (user_id,))
        permissions = json.loads(perms_data[0][0]) if perms_data else []
    except Exception as e:
        print(f"Erreur lors de la récupération des permissions: {e}")
        permissions = []
    
    # Liste des permissions disponibles dans le système
    all_permissions = [
        {"id": "create_ticket", "name": "Créer des tickets", "description": "Permet de créer de nouveaux tickets"},
        {"id": "edit_ticket", "name": "Modifier des tickets", "description": "Permet de modifier tous les tickets"},
        {"id": "close_ticket", "name": "Fermer des tickets", "description": "Permet de fermer tous les tickets"},
        {"id": "delete_ticket", "name": "Supprimer des tickets", "description": "Permet de supprimer des tickets"},
        {"id": "manage_inventory", "name": "Gérer l'inventaire", "description": "Permet d'ajouter/modifier/supprimer des éléments d'inventaire"},
        {"id": "view_activity", "name": "Voir les activités", "description": "Permet de voir toutes les activités des utilisateurs"},
        {"id": "manage_users", "name": "Gérer les utilisateurs", "description": "Permet de gérer les utilisateurs (admin uniquement)"}
    ]
    
    return render_template('admin/edit_user.html', 
                          user=user,
                          user_dict=user_dict,
                          permissions=permissions,
                          all_permissions=all_permissions,
                          now=datetime.now())

@admin_bp.route('/users/reset_password/<user_id>', methods=['POST'])
def reset_password(user_id):
    """Réinitialise le mot de passe d'un utilisateur"""
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not new_password or not confirm_password:
            flash("Veuillez remplir tous les champs", "error")
            return redirect(url_for('admin.edit_user', user_id=user_id))
        
        if new_password != confirm_password:
            flash("Les mots de passe ne correspondent pas", "error")
            return redirect(url_for('admin.edit_user', user_id=user_id))
            
        try:
            # Hacher le mot de passe avec SHA256
            hashed_password = hashlib.sha256(new_password.encode()).hexdigest()
            
            # Mettre à jour le mot de passe de l'utilisateur
            get_db("UPDATE USEUR SET hashed_password = %s WHERE ID = %s", 
                  (hashed_password, user_id))
            
            log_activity(session.get('user_id'), 'update', 'user', f"Réinitialisation du mot de passe pour l'utilisateur {user_id}")
            flash("Le mot de passe a été réinitialisé avec succès", "success")
        except Exception as e:
            flash(f"Erreur lors de la réinitialisation du mot de passe: {str(e)}", "error")
        
        return redirect(url_for('admin.edit_user', user_id=user_id))

@admin_bp.route('/settings')
def settings():
    """Paramètres généraux du système"""
    # Récupérer les paramètres actuels
    try:
        settings = get_db("SELECT * FROM system_settings")
        current_settings = {}
        for setting in settings:
            current_settings[setting[0]] = setting[1]
    except:
        current_settings = {}
        
        # Création de la table des paramètres si elle n'existe pas
        get_db("""
            CREATE TABLE IF NOT EXISTS system_settings (
                setting_key VARCHAR(255) PRIMARY KEY,
                setting_value TEXT
            )
        """)
    
    return render_template('admin/settings.html', settings=current_settings, now=datetime.now())

@admin_bp.route('/settings/update', methods=['POST'])
def update_settings():
    """Mettre à jour les paramètres du système"""
    # Récupérer tous les paramètres du formulaire
    allow_registration = request.form.get('allow_registration', '0')
    allow_ticket_creation = request.form.get('allow_ticket_creation', '0')
    default_user_role = request.form.get('default_user_role', 'user')
    system_name = request.form.get('system_name', 'GLPI')
    
    # Enregistrer les paramètres dans la base de données
    try:
        settings = {
            'allow_registration': allow_registration,
            'allow_ticket_creation': allow_ticket_creation,
            'default_user_role': default_user_role,
            'system_name': system_name
        }
        
        for key, value in settings.items():
            existing = get_db("SELECT * FROM system_settings WHERE setting_key = %s", (key,))
            if existing:
                get_db("UPDATE system_settings SET setting_value = %s WHERE setting_key = %s", (value, key))
            else:
                get_db("INSERT INTO system_settings (setting_key, setting_value) VALUES (%s, %s)", (key, value))
        
        log_activity(session.get('user_id'), 'update', 'settings', f"Mise à jour des paramètres système")
        flash("Paramètres mis à jour avec succès", "success")
    except Exception as e:
        flash(f"Erreur lors de la mise à jour des paramètres: {str(e)}", "error")
    
    return redirect(url_for('admin.settings'))

@admin_bp.route('/logs')
def logs():
    """Affiche les journaux d'activité du système"""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page
    
    # Récupérer les journaux d'activité
    try:
        logs = get_db(f"""
            SELECT a.id, a.user_id, u.name, a.action_type, a.module, a.description, a.timestamp
            FROM activity_logs a
            LEFT JOIN USEUR u ON a.user_id = u.ID
            ORDER BY a.timestamp DESC
            LIMIT {per_page} OFFSET {offset}
        """)
        
        # Compter le nombre total de journaux
        total_count = get_db("SELECT COUNT(*) FROM activity_logs")[0][0]
        
    except Exception as e:
        logs = []
        total_count = 0
        flash(f"Erreur lors de la récupération des journaux: {str(e)}", "error")
    
    total_pages = (total_count + per_page - 1) // per_page
    
    return render_template('admin/logs.html', 
                          logs=logs, 
                          page=page,
                          total_pages=total_pages,
                          now=datetime.now())