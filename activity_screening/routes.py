from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from utils.db import get_db, log_activity
import os
from datetime import datetime, timedelta
import csv
from io import StringIO

# Création du Blueprint pour les routes liées au suivi d'activités
activity_bp = Blueprint('activity', __name__, template_folder='templates')

def get_active_users():
    """Récupère le nombre d'utilisateurs actifs dans les 7 derniers jours"""
    active_users = get_db("SELECT COUNT(DISTINCT ID) FROM USEUR WHERE derniere_connexion > (NOW() - INTERVAL 7 DAY)")
    return active_users[0][0] if active_users else 0

@activity_bp.route('/')
def index():
    """Page principale du module Activity Screening"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    try:
        # S'assurer que la table activity_tasks existe
        get_db("""
            CREATE TABLE IF NOT EXISTS activity_tasks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                assigned_to VARCHAR(255),
                status VARCHAR(50) DEFAULT 'pending',
                priority INT DEFAULT 3,
                progress INT DEFAULT 0,
                created_by VARCHAR(255),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                deadline DATE,
                parent_task_id INT,
                INDEX idx_status (status),
                INDEX idx_assigned_to (assigned_to)
            )
        """)
        
        # Récupérer les tâches
        tasks = get_db("""
            SELECT t.*, u.name as assigned_name, c.name as creator_name
            FROM activity_tasks t
            LEFT JOIN USEUR u ON t.assigned_to = u.ID
            LEFT JOIN USEUR c ON t.created_by = c.ID
            ORDER BY t.priority DESC, t.created_at DESC
        """)
        
        # Formater les tâches pour l'affichage
        formatted_tasks = []
        for task in tasks:
            formatted_tasks.append({
                'id': task[0],
                'title': task[1],
                'description': task[2],
                'assigned_to': task[3],
                'assigned_name': task[10] or "Non assigné",
                'status': task[4],
                'priority': task[5],
                'progress': task[6],
                'created_by': task[7],
                'creator_name': task[11] or "Utilisateur inconnu",
                'created_at': task[8],
                'deadline': task[10]
            })
        
        # Récupérer les statistiques pour le tableau de bord
        active_users = get_active_users()
        open_tickets = get_db("SELECT COUNT(*) FROM TIQUE WHERE status != 'closed'")
        
        # Calcul du temps moyen de résolution (en heures)
        resolution_data = get_db("""
            SELECT AVG(TIMESTAMPDIFF(HOUR, created_at, resolved_at)) 
            FROM TIQUE 
            WHERE status = 'closed' 
            AND resolved_at IS NOT NULL
        """)
        
        avg_time = resolution_data[0][0] if resolution_data and resolution_data[0][0] else 0
        if avg_time:
            avg_resolution_time = f"{int(avg_time)} heures"
        else:
            avg_resolution_time = "N/A"
            
        # Nombre total de matériel inventorié
        hardware_count = get_db("SELECT COUNT(*) FROM HARDWARE")
        
        # Statistiques pour le template
        stats = {
            "active_users": active_users,
            "open_tickets": open_tickets[0][0] if open_tickets else 0,
            "avg_resolution_time": avg_resolution_time,
            "total_hardware": hardware_count[0][0] if hardware_count else 0
        }
        
        # Données pour les graphiques
        ticket_activity_data = {
            "labels": ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"],
            "created": [5, 8, 12, 7, 10, 3, 2],  # Exemple de données
            "closed": [3, 5, 8, 6, 9, 2, 1]      # Exemple de données
        }
        
        ticket_distribution_data = {
            "labels": ["En attente", "En cours", "À vérifier", "Résolu", "Fermé"],
            "data": [10, 15, 8, 12, 20]  # Exemple de données
        }
        
        # Récupérer quelques logs pour le tableau
        logs = get_db("""
            SELECT * FROM activity_logs
            ORDER BY timestamp DESC
            LIMIT 20
        """)
        
        if not logs:
            logs = []
        
        log_activity(user_id, 'view', 'activity', "Consultation du tableau d'activités")
    except Exception as e:
        flash(f"Erreur lors de la récupération des activités: {str(e)}", "error")
        formatted_tasks = []
        stats = {
            "active_users": 0,
            "open_tickets": 0, 
            "avg_resolution_time": "N/A",
            "total_hardware": 0
        }
        ticket_activity_data = {
            "labels": ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"],
            "created": [0, 0, 0, 0, 0, 0, 0],
            "closed": [0, 0, 0, 0, 0, 0, 0]
        }
        ticket_distribution_data = {
            "labels": ["En attente", "En cours", "À vérifier", "Résolu", "Fermé"],
            "data": [0, 0, 0, 0, 0]
        }
        logs = []
    
    return render_template('activity_screening/index.html', 
                          tasks=formatted_tasks, 
                          now=datetime.now(),
                          stats=stats,
                          ticket_activity_data=ticket_activity_data,
                          ticket_distribution_data=ticket_distribution_data,
                          logs=logs)

@activity_bp.route('/dashboard')
def dashboard():
    """Affiche le tableau de bord avec les statistiques et les tâches"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    # Récupérer les tâches et les statistiques
    tasks = get_db("SELECT * FROM activity_tasks")
    active_users = get_active_users()
    open_tickets = get_db("SELECT COUNT(*) FROM TIQUE WHERE status != 'closed'")
    
    # Calculer le temps moyen de résolution (en heures)
    resolution_data = get_db("""
        SELECT AVG(TIMESTAMPDIFF(HOUR, created_at, resolved_at)) 
        FROM TIQUE 
        WHERE status = 'closed' 
        AND resolved_at IS NOT NULL
    """)
    
    avg_time = resolution_data[0][0] if resolution_data and resolution_data[0][0] else 0
    avg_resolution_time = f"{int(avg_time)} heures" if avg_time else "N/A"
    
    # Statistiques pour le template
    stats = {
        "active_users": active_users,
        "open_tickets": open_tickets[0][0] if open_tickets else 0,
        "avg_resolution_time": avg_resolution_time,
    }
    
    return render_template('activity_screening/dashboard.html', 
                          tasks=tasks, 
                          stats=stats, 
                          now=datetime.now())

def get_tasks_with_subtasks():
    """Récupère les tâches avec leurs sous-tâches"""
    tasks = get_db("""
        SELECT t.*, u.name as assigned_name 
        FROM activity_tasks t
        LEFT JOIN USEUR u ON t.assigned_to = u.ID
        WHERE t.parent_task_id IS NULL
        ORDER BY t.priority DESC, t.created_at DESC
    """)
    
    formatted_tasks = []
    for task in tasks:
        # Récupérer les sous-tâches
        subtasks = get_db("""
            SELECT t.*, u.name as assigned_name
            FROM activity_tasks t
            LEFT JOIN USEUR u ON t.assigned_to = u.ID
            WHERE t.parent_task_id = %s
            ORDER BY t.created_at ASC
        """, (task[0],))
        
        formatted_subtasks = []
        for subtask in subtasks:
            formatted_subtasks.append({
                'id': subtask[0],
                'title': subtask[1],
                'assigned_name': subtask[10] or "Non assigné",
                'status': subtask[4]
            })
        
        formatted_tasks.append({
            'id': task[0],
            'title': task[1],
            'description': task[2],
            'assigned_name': task[10] or "Non assigné",
            'status': task[4],
            'status_class': get_status_class(task[4]),
            'progress': task[6],
            'subtasks': formatted_subtasks
        })
    
    return formatted_tasks

def get_current_course():
    """Récupère le cours actuel depuis EcoleDirecte"""
    now = datetime.now()
    
    course = get_db("""
        SELECT matiere, salle, groupe, professeur
        FROM ecoledirecte_emploi_du_temps
        WHERE date_debut <= NOW()
        AND date_fin > NOW()
        ORDER BY date_debut ASC
        LIMIT 1
    """)
    
    if course and course[0]:
        return {
            'name': course[0][0],
            'room': course[0][1],
            'class': course[0][2],
            'teacher': course[0][3]
        }
    return None

def get_next_courses():
    """Récupère les prochains cours de la journée depuis EcoleDirecte"""
    now = datetime.now()
    
    courses = get_db("""
        SELECT matiere, salle, groupe, professeur, date_debut, date_fin
        FROM ecoledirecte_emploi_du_temps
        WHERE date_debut > NOW()
        AND DATE(date_debut) = CURRENT_DATE
        ORDER BY date_debut ASC
        LIMIT 5
    """)
    
    formatted_courses = []
    for course in courses:
        start = course[4]
        end = course[5]
        duration = end - start
        
        formatted_courses.append({
            'name': course[0],
            'room': course[1],
            'class': course[2],
            'teacher': course[3],
            'time': start.strftime('%H:%M'),
            'duration': f"{duration.seconds // 3600}h{(duration.seconds % 3600) // 60:02d}"
        })
    
    return formatted_courses

def get_status_class(status):
    """Retourne la classe CSS appropriée pour un statut donné"""
    status_classes = {
        'pending': 'secondary',
        'in_progress': 'primary',
        'completed': 'success',
        'blocked': 'danger',
        'review': 'warning'
    }
    return status_classes.get(status, 'secondary')

@activity_bp.route('/live')
def live():
    """Affichage en direct des activités"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    try:
        tasks = get_tasks_with_subtasks()
        current_course = get_current_course()
        next_courses = get_next_courses()
        
        log_activity(user_id, 'view', 'activity', "Visualisation de l'affichage en direct")
        
        return render_template('activity_screening/live.html',
                             tasks=tasks,
                             current_course=current_course,
                             next_courses=next_courses)
    except Exception as e:
        flash(f"Erreur lors du chargement de l'affichage en direct: {str(e)}", "error")
        return redirect(url_for('activity.index'))

@activity_bp.route('/api/live-data')
def get_live_data():
    """API pour récupérer les données en temps réel"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        return jsonify({
            'tasks': get_tasks_with_subtasks(),
            'current_course': get_current_course(),
            'next_courses': get_next_courses()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@activity_bp.route('/export-logs')
def export_logs():
    """Export activity logs to CSV"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    try:
        # Fetch all logs
        logs = get_db("""
            SELECT * FROM activity_logs
            ORDER BY timestamp DESC
        """)
        
        # Create CSV in memory
        si = StringIO()
        writer = csv.writer(si)
        writer.writerow(['User ID', 'Action', 'Module', 'Description', 'Timestamp'])  # Headers
        
        for log in logs:
            writer.writerow(log)
        
        # Create the response
        output = si.getvalue()
        si.close()
        
        log_activity(user_id, 'export', 'activity', "Export des logs d'activité")
        
        return send_file(
            StringIO(output),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'activity_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
        
    except Exception as e:
        flash(f"Erreur lors de l'export des logs: {str(e)}", "error")
        return redirect(url_for('activity.index'))