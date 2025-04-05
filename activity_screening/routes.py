from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from utils.db import get_db, log_activity
import os
from datetime import datetime
import csv
from io import StringIO

# Création du Blueprint pour les routes liées au suivi d'activités
activity_bp = Blueprint('activity', __name__, template_folder='templates')

@activity_bp.route('/')
def index():
    """Page principale du module Activity Screening"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    # Récupérer les activités directement depuis notre base de données au lieu d'utiliser l'API externe
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
        active_users = get_db("SELECT COUNT(DISTINCT ID) FROM USEUR WHERE last_login > (NOW() - INTERVAL 7 DAY)")
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
            "active_users": active_users[0][0] if active_users else 0,
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

@activity_bp.route('/live')
def live():
    """Affichage en temps réel des activités"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    log_activity(user_id, 'view', 'activity', "Visualisation des activités en direct")
    
    return render_template('activity_screening/live.html', now=datetime.now())

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