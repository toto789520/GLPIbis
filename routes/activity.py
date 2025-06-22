from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from utils.db_manager import get_db
from utils.logger import get_logger
from datetime import datetime

activity_bp = Blueprint('activity', __name__, url_prefix='/activity')
logger = get_logger()

@activity_bp.route('/')
def index():
    """Page d'accueil des activités"""
    try:
        # Créer la table activities si elle n'existe pas
        get_db("""
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                type TEXT DEFAULT 'general',
                status TEXT DEFAULT 'active',
                assigned_to TEXT,
                due_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Récupérer les activités
        activities = get_db("SELECT * FROM activities ORDER BY created_at DESC") or []
        
        # Statistiques
        stats = {
            'total_activities': len(activities),
            'active_activities': len([a for a in activities if a[3] == 'active']),
            'completed_activities': len([a for a in activities if a[3] == 'completed']),
            'overdue_activities': 0
        }
        
        logger.debug(f"Affichage de {len(activities)} activités")
        return render_template('activity/index.html', 
                             activities=activities, 
                             stats=stats,
                             now=datetime.now())
                             
    except Exception as e:
        logger.error(f"Erreur lors du chargement des activités: {e}")
        flash("Erreur lors du chargement des activités", "error")
        return render_template('activity/index.html', 
                             activities=[], 
                             stats={'total_activities': 0, 'active_activities': 0, 'completed_activities': 0, 'overdue_activities': 0},
                             now=datetime.now())

@activity_bp.route('/create', methods=['GET', 'POST'])
def create_activity():
    """Créer une nouvelle activité"""
    if request.method == 'POST':
        try:
            title = request.form.get('title')
            description = request.form.get('description')
            activity_type = request.form.get('type', 'general')
            assigned_to = request.form.get('assigned_to')
            due_date = request.form.get('due_date')
            
            if not title:
                flash("Le titre est obligatoire", "error")
                return render_template('activity/create.html')
            
            get_db("""
                INSERT INTO activities (title, description, type, assigned_to, due_date)
                VALUES (?, ?, ?, ?, ?)
            """, (title, description, activity_type, assigned_to, 
                  due_date if due_date else None))
            
            logger.info(f"Nouvelle activité créée: {title}")
            flash(f"Activité '{title}' créée avec succès", "success")
            return redirect(url_for('activity.index'))
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'activité: {e}")
            flash(f"Erreur lors de la création: {str(e)}", "error")
    
    return render_template('activity/create.html', now=datetime.now())

@activity_bp.route('/view/<int:activity_id>')
def view_activity(activity_id):
    """Voir les détails d'une activité"""
    try:
        activity = get_db("SELECT * FROM activities WHERE id = ?", (activity_id,))
        if not activity:
            flash("Activité non trouvée", "error")
            return redirect(url_for('activity.index'))
        
        return render_template('activity/view.html', 
                             activity=activity[0], 
                             now=datetime.now())
                             
    except Exception as e:
        logger.error(f"Erreur lors de la visualisation de l'activité {activity_id}: {e}")
        flash("Erreur lors du chargement de l'activité", "error")
        return redirect(url_for('activity.index'))

@activity_bp.route('/update/<int:activity_id>', methods=['POST'])
def update_activity(activity_id):
    """Mettre à jour une activité"""
    try:
        status = request.form.get('status')
        
        get_db("""
            UPDATE activities 
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (status, activity_id))
        
        flash("Activité mise à jour avec succès", "success")
        return redirect(url_for('activity.view_activity', activity_id=activity_id))
        
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour de l'activité {activity_id}: {e}")
        flash("Erreur lors de la mise à jour", "error")
        return redirect(url_for('activity.view_activity', activity_id=activity_id))

@activity_bp.route('/delete/<int:activity_id>', methods=['POST'])
def delete_activity(activity_id):
    """Supprimer une activité"""
    try:
        get_db("DELETE FROM activities WHERE id = ?", (activity_id,))
        flash("Activité supprimée avec succès", "success")
        return redirect(url_for('activity.index'))
        
    except Exception as e:
        logger.error(f"Erreur lors de la suppression de l'activité {activity_id}: {e}")
        flash("Erreur lors de la suppression", "error")
        return redirect(url_for('activity.index'))
