from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from utils.logger import get_logger
from utils.db_manager import get_db
from datetime import datetime

main_bp = Blueprint('main', __name__)
logger = get_logger()

@main_bp.route('/')
def index():
    """Page d'accueil principale"""
    try:
        # Statistiques générales pour le tableau de bord
        stats = {
            'total_tickets': 0,
            'total_inventory': 0,
            'total_activities': 0,
            'recent_activities': []
        }
        
        # Récupérer les statistiques des tickets
        try:
            tickets_result = get_db("SELECT COUNT(*) FROM tiqué")
            stats['total_tickets'] = tickets_result[0][0] if tickets_result else 0
        except:
            pass
        
        # Récupérer les statistiques de l'inventaire
        try:
            inventory_result = get_db("SELECT COUNT(*) FROM inventory")
            stats['total_inventory'] = inventory_result[0][0] if inventory_result else 0
        except:
            pass
        
        # Récupérer les statistiques des activités
        try:
            activities_result = get_db("SELECT COUNT(*) FROM activities")
            stats['total_activities'] = activities_result[0][0] if activities_result else 0
        except:
            pass
        
        # Récupérer les activités récentes
        try:
            recent_activities = get_db("""
                SELECT title, type, created_at 
                FROM activities 
                ORDER BY created_at DESC 
                LIMIT 5
            """)
            stats['recent_activities'] = recent_activities or []
        except:
            pass
        
        logger.debug(f"Affichage du tableau de bord principal avec stats: {stats}")
        return render_template('index.html', stats=stats, now=datetime.now())
        
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la page d'accueil: {e}")
        return render_template('index.html', 
                             stats={'total_tickets': 0, 'total_inventory': 0, 'total_activities': 0, 'recent_activities': []},
                             now=datetime.now())

@main_bp.route('/dashboard')
def dashboard():
    """Tableau de bord détaillé"""
    return redirect(url_for('main.index'))

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion"""
    if request.method == 'POST':
        # Logique de connexion à implémenter
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Pour l'instant, redirection simple
        flash("Fonctionnalité de connexion en cours de développement", "info")
        return redirect(url_for('main.index'))
    
    return render_template('auth/login.html', now=datetime.now())

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Page d'inscription"""
    if request.method == 'POST':
        # Logique d'inscription à implémenter
        flash("Fonctionnalité d'inscription en cours de développement", "info")
        return redirect(url_for('main.login'))
    
    return render_template('auth/register.html', now=datetime.now())

@main_bp.route('/logout')
def logout():
    """Déconnexion"""
    session.clear()
    flash("Vous avez été déconnecté", "info")
    return redirect(url_for('main.index'))

@main_bp.route('/about')
def about():
    """Page À propos"""
    try:
        return render_template('about.html', now=datetime.now())
    except Exception as e:
        logger.error(f"Erreur lors du chargement de la page À propos: {e}")
        return redirect(url_for('main.index'))
