from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from utils.db import get_db, log_activity
import os
from datetime import datetime

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
        
        log_activity(user_id, 'view', 'activity', "Consultation du tableau d'activités")
    except Exception as e:
        flash(f"Erreur lors de la récupération des activités: {str(e)}", "error")
        formatted_tasks = []
    
    return render_template('activity_screening/index.html', tasks=formatted_tasks, now=datetime.now())

@activity_bp.route('/live')
def live():
    """Affichage en temps réel des activités"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    log_activity(user_id, 'view', 'activity', "Visualisation des activités en direct")
    
    return render_template('activity_screening/live.html', now=datetime.now())

@activity_bp.route('/create', methods=['GET', 'POST'])
def create_task():
    """Créer une nouvelle tâche"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        assigned_to = request.form.get('assigned_to')
        priority = request.form.get('priority', 3)
        deadline = request.form.get('deadline')
        
        if not title:
            flash("Le titre est obligatoire", "error")
            return render_template('activity_screening/create_task.html', now=datetime.now())
        
        try:
            # Insérer la nouvelle tâche
            task_data = {
                'title': title,
                'description': description,
                'assigned_to': assigned_to if assigned_to else None,
                'priority': priority,
                'deadline': deadline if deadline else None,
                'created_by': user_id
            }
            
            get_db("""
                INSERT INTO activity_tasks (title, description, assigned_to, priority, created_by, deadline)
                VALUES (%(title)s, %(description)s, %(assigned_to)s, %(priority)s, %(created_by)s, %(deadline)s)
            """, task_data)
            
            log_activity(user_id, 'create', 'activity', f"Création d'une nouvelle tâche: {title}")
            flash("La tâche a été créée avec succès", "success")
            return redirect(url_for('activity.index'))
            
        except Exception as e:
            flash(f"Erreur lors de la création de la tâche: {str(e)}", "error")
    
    # Récupérer la liste des utilisateurs pour l'assignation
    users = get_db("SELECT ID, name FROM USEUR ORDER BY name")
    
    return render_template('activity_screening/create_task.html', users=users, now=datetime.now())

@activity_bp.route('/task/<int:task_id>')
def view_task(task_id):
    """Afficher les détails d'une tâche"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    try:
        # Récupérer les informations de la tâche
        task_data = get_db("""
            SELECT t.*, u.name as assigned_name, c.name as creator_name
            FROM activity_tasks t
            LEFT JOIN USEUR u ON t.assigned_to = u.ID
            LEFT JOIN USEUR c ON t.created_by = c.ID
            WHERE t.id = %s
        """, (task_id,))
        
        if not task_data:
            flash("Tâche introuvable", "error")
            return redirect(url_for('activity.index'))
            
        task = task_data[0]
        
        # Récupérer les commentaires de la tâche
        comments = get_db("""
            SELECT c.*, u.name as author_name
            FROM activity_task_comments c
            LEFT JOIN USEUR u ON c.user_id = u.ID
            WHERE c.task_id = %s
            ORDER BY c.created_at
        """, (task_id,))
        
        log_activity(user_id, 'view', 'activity', f"Consultation de la tâche #{task_id}")
        
        formatted_task = {
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
        }
        
        return render_template('activity_screening/view_task.html', 
                              task=formatted_task, 
                              comments=comments,
                              now=datetime.now())
    
    except Exception as e:
        flash(f"Erreur lors de la récupération de la tâche: {str(e)}", "error")
        return redirect(url_for('activity.index'))

@activity_bp.route('/task/<int:task_id>/update', methods=['POST'])
def update_task(task_id):
    """Mettre à jour une tâche"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    action = request.form.get('action')
    
    try:
        if action == 'update_status':
            new_status = request.form.get('status')
            get_db("UPDATE activity_tasks SET status = %s WHERE id = %s", (new_status, task_id))
            log_activity(user_id, 'update', 'activity', f"Mise à jour du statut de la tâche #{task_id} en '{new_status}'")
            
        elif action == 'update_progress':
            progress = request.form.get('progress')
            get_db("UPDATE activity_tasks SET progress = %s WHERE id = %s", (progress, task_id))
            log_activity(user_id, 'update', 'activity', f"Mise à jour de la progression de la tâche #{task_id} à {progress}%")
            
        elif action == 'add_comment':
            comment = request.form.get('comment')
            if comment:
                # S'assurer que la table des commentaires existe
                get_db("""
                    CREATE TABLE IF NOT EXISTS activity_task_comments (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        task_id INT NOT NULL,
                        user_id VARCHAR(255) NOT NULL,
                        comment TEXT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_task_id (task_id)
                    )
                """)
                
                get_db("""
                    INSERT INTO activity_task_comments (task_id, user_id, comment)
                    VALUES (%s, %s, %s)
                """, (task_id, user_id, comment))
                
                log_activity(user_id, 'comment', 'activity', f"Ajout d'un commentaire à la tâche #{task_id}")
        
        flash("Mise à jour effectuée avec succès", "success")
    
    except Exception as e:
        flash(f"Erreur lors de la mise à jour: {str(e)}", "error")
    
    return redirect(url_for('activity.view_task', task_id=task_id))

@activity_bp.route('/api/tasks')
def api_tasks():
    """API pour récupérer les tâches (utilisé par d'autres modules)"""
    try:
        tasks = get_db("""
            SELECT t.*, u.name as assigned_name, c.name as creator_name
            FROM activity_tasks t
            LEFT JOIN USEUR u ON t.assigned_to = u.ID
            LEFT JOIN USEUR c ON t.created_by = c.ID
            ORDER BY t.priority DESC, t.created_at DESC
        """)
        
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
                'created_at': str(task[8]),
                'deadline': str(task[10]) if task[10] else None
            })
        
        return jsonify({'tasks': formatted_tasks})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500