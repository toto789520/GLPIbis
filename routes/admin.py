from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
import logging
import os
import sqlite3
from datetime import datetime
# Import direct du gestionnaire de base de données
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from utils.db_manager import DBManager
except ImportError as e:
    print(f"Erreur d'import DBManager: {e}")
    DBManager = None

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
logger = logging.getLogger('glpibis')

def get_db():
    """Obtenir une instance de DBManager"""
    if DBManager is None:
        raise ImportError("DBManager n'a pas pu être importé")
    return DBManager()

def get_db_stats():
    """Récupérer les statistiques de la base de données"""
    try:
        db = get_db()
        
        # Statistiques des tickets
        try:
            tickets_result = db.execute_query("SELECT COUNT(*) FROM `tiqué`")
            total_tickets = tickets_result[0][0] if tickets_result else 0
        except Exception:
            total_tickets = 0
        
        # Statistiques de l'inventaire  
        try:
            inventory_result = db.execute_query("SELECT COUNT(*) FROM inventory")
            total_inventory = inventory_result[0][0] if inventory_result else 0
        except Exception:
            total_inventory = 0
        
        # Statistiques des activités
        try:
            activities_result = db.execute_query("SELECT COUNT(*) FROM activity_logs")
            total_activities = activities_result[0][0] if activities_result else 0
        except Exception:
            total_activities = 0
        
        # Statistiques des utilisateurs
        try:
            users_result = db.execute_query("SELECT COUNT(*) FROM USEUR")
            total_users = users_result[0][0] if users_result else 0
        except Exception:
            total_users = 0
        
        # Taille de la base de données
        database_size = 0
        db_path = os.path.join('database', 'glpibis.sqlite')
        if os.path.exists(db_path):
            database_size = os.path.getsize(db_path)
        
        return {
            'total_tickets': total_tickets,
            'total_inventory': total_inventory, 
            'total_activities': total_activities,
            'total_users': total_users,
            'database_size': database_size
        }
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution de la requête: {e}")
        return {
            'total_tickets': 0,
            'total_inventory': 0,
            'total_activities': 0,
            'total_users': 0,
            'database_size': 0
        }

@admin_bp.before_request
def before_request():
    """Fonction exécutée avant chaque requête"""
    logger.debug("Avant la requête")
    #Vérifier si user est un admin
    if 'user' not in session or session.get('role') != 'admin':
        logger.warning("Tentative d'accès à une page admin sans être admin")
        flash("Vous n'avez pas les droits nécessaires pour accéder à cette page.", "error")
        return redirect(url_for('index'))
    else:
        logger.debug("Utilisateur admin autorisé à accéder à la page")
        # Log l'accès à la page admin
        logger.info(f"Accès à la page admin par {session.get('user_id')} à {datetime.now()}")

@admin_bp.route('/')
def index():
    """Page principale d'administration"""
    try:
        # Obtenir les statistiques de manière sécurisée
        try:
            stats = get_db_stats()
            if not isinstance(stats, dict):
                stats = {
                    'total_tickets': 0,
                    'total_inventory': 0,
                    'total_activities': 0,
                    'total_users': 0,
                    'database_size': 0
                }
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des statistiques: {e}")
            stats = {
                'total_tickets': 0,
                'total_inventory': 0,
                'total_activities': 0,
                'total_users': 0,
                'database_size': 0
            }
        
        logger.debug(f"Affichage des statistiques admin: {stats}")
        
        return render_template('admin/index.html',
                             stats=stats,
                             current_time=datetime.now())
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la page admin: {e}")
        flash("Erreur lors du chargement des données d'administration", "error")
        # Retourner une réponse d'erreur valide
        try:
            return render_template('admin/index.html',
                                 stats={'total_tickets': 0, 'total_inventory': 0, 'total_activities': 0, 'total_users': 0, 'database_size': 0},
                                 current_time=datetime.now())
        except Exception as final_error:
            logger.error(f"Erreur finale lors du rendu du template: {final_error}")
            # En dernier recours, retourner une réponse HTML simple
            return "<h1>Erreur de chargement de la page d'administration</h1><p>Veuillez contacter l'administrateur.</p>", 500

@admin_bp.route('/users')
def users():
    """Page de gestion des utilisateurs"""
    try:
        logger.debug("Route /admin/users appelée")
        db = get_db()
        
        # Récupérer tous les utilisateurs
        try:
            users_data = db.execute_query("SELECT ID, email, name, creation_date, role FROM USEUR ORDER BY email")
            if not users_data:
                users_data = []
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des utilisateurs: {e}")
            users_data = []
        
        return render_template('admin/users.html', users=users_data)
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la page utilisateurs: {e}")
        flash('Erreur lors du chargement des utilisateurs', 'error')
        return redirect(url_for('admin.index'))

@admin_bp.route('/logs')
def logs():
    """Page de consultation des logs"""
    try:
        logger.debug("Route /admin/logs appelée")
        
        # Lire les logs récents
        log_file = os.path.join('logs', 'glpibis--2025-06-21.log')
        logs_content = []
        
        if os.path.exists(log_file):
            try:
                # Essayer d'abord avec UTF-8
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    # Prendre les 100 dernières lignes
                    logs_content = lines[-100:] if len(lines) > 100 else lines
            except UnicodeDecodeError:
                # Si UTF-8 ne fonctionne pas, essayer avec latin-1
                with open(log_file, 'r', encoding='latin-1') as f:
                    lines = f.readlines()
                    # Prendre les 100 dernières lignes
                    logs_content = lines[-100:] if len(lines) > 100 else lines
        
        return render_template('admin/logs.html', logs=logs_content)
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la page logs: {e}")
        flash('Erreur lors du chargement des logs', 'error')
        return redirect(url_for('admin.index'))

@admin_bp.route('/database')
def database():
    """Page de gestion de la base de données"""
    try:
        db = get_db()
        
        # Informations sur les tables
        table_queries = [
            ('USEUR', "SELECT COUNT(*) FROM USEUR"),
            ('tiqué', "SELECT COUNT(*) FROM `tiqué`"),
            ('inventory', "SELECT COUNT(*) FROM inventory"),
            ('activity_logs', "SELECT COUNT(*) FROM activity_logs"),
            ('sessions', "SELECT COUNT(*) FROM sessions")
        ]
        
        table_info = []
        for table_name, query in table_queries:
            try:
                result = db.execute_query(query)
                count = result[0][0] if result else 0
                table_info.append({'name': table_name, 'count': count})
            except Exception as e:
                logger.error(f"Erreur lors du comptage pour {table_name}: {e}")
                table_info.append({'name': table_name, 'count': 0})
        
        # Taille de la base de données
        db_path = os.path.join('database', 'glpibis.sqlite')
        db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0
        
        return render_template('admin/database.html',
                             table_info=table_info,
                             db_size=db_size,
                             current_time=datetime.now())
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la page base de données: {e}")
        return render_template('admin/database.html',
                             table_info=[],
                             db_size=0,
                             current_time=datetime.now())

@admin_bp.route('/settings')
def settings():
    """Page des paramètres système"""
    try:
        return render_template('admin/settings.html', current_time=datetime.now())
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la page paramètres: {e}")
        flash('Erreur lors du chargement des paramètres', 'error')
        return redirect(url_for('admin.index'))

@admin_bp.route('/system-info')
def system_info():
    """Page d'informations système"""
    try:
        try:
            import psutil
            import platform
            
            # Informations système
            system_info_data = {
                'platform': platform.system(),
                'platform_release': platform.release(),
                'platform_version': platform.version(),
                'architecture': platform.machine(),
                'hostname': platform.node(),
                'processor': platform.processor(),
                'ram': str(round(psutil.virtual_memory().total / (1024.0 **3)))+" GB",
                'cpu_count': psutil.cpu_count(),
                'cpu_usage': psutil.cpu_percent(),
                'memory_usage': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent if platform.system() != 'Windows' else psutil.disk_usage('C:\\').percent
            }
        except ImportError:
            # Si psutil n'est pas installé
            import platform
            system_info_data = {
                'platform': platform.system(),
                'platform_release': platform.release(),
                'architecture': platform.machine(),
                'hostname': platform.node(),
                'processor': platform.processor(),
            }
        
        return render_template('admin/system_info.html',
                             system_info=system_info_data,
                             current_time=datetime.now())
    except Exception as e:
        logger.error(f"Erreur lors du chargement des informations système: {e}")
        return render_template('admin/system_info.html',
                             system_info={},
                             current_time=datetime.now())

# Ajouter une route de test pour vérifier que le blueprint fonctionne
@admin_bp.route('/test')
def test():
    """Route de test pour vérifier le blueprint admin"""
    return "Blueprint admin fonctionne correctement!", 200
