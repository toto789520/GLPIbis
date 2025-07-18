from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, send_file
import app
from utils.db_manager import get_db, log_activity
import os
from datetime import datetime, timedelta
import csv
from io import StringIO

# Création du Blueprint pour les routes liées au suivi d'activités
activity_bp = Blueprint('activity_screening', __name__, url_prefix='/activity')

@activity_bp.route('/')
def index():
    """Page principale des activités pour les utilisateurs connectés"""
    if not session.get('user_id'):
        flash("Vous devez être connecté pour accéder à cette page.", "warning")
        return redirect(url_for('login'))
    
    # Récupérer les activités des dernières 24 heures
    activities = get_recent_activities(hours=24)
    stats = get_activity_stats()
    
    # Données pour les graphiques
    ticket_activity_data = get_ticket_activity_data()
    ticket_distribution_data = get_ticket_distribution_data()
    
    app.app_logger.debug(f"activités récupérées: {activities}, stats: {stats},ticket_activity_data: {ticket_activity_data}, ticket_distribution_data: {ticket_distribution_data},")
    return render_template('activity_screening/index.html', 
                          activities=activities, 
                          stats=stats,
                          title="Activités récentes",
                          ticket_activity_data=ticket_activity_data,
                          ticket_distribution_data=ticket_distribution_data)

@activity_bp.route('/kiosk')
def kiosk():
    """Page d'affichage des activités en mode kiosk (sans authentification requise)"""
    # Cette route est spéciale car elle est accessible sans connexion pour l'affichage sur écran TV
    
    # Récupérer les activités des dernières 24 heures
    activities = get_recent_activities(hours=24)
    stats = get_activity_stats()
    
    return render_template('activity_screening/kiosk.html', 
                          activities=activities, 
                          stats=stats)

@activity_bp.route('/data')
def get_data():
    """API pour récupérer les données d'activité (pour les mises à jour AJAX)"""
    if not session.get('user_id'):
        return jsonify({'error': 'Non autorisé'}), 401
    
    hours = int(request.args.get('hours', 24))
    activities = get_recent_activities(hours=hours)
    stats = get_activity_stats()
    
    return jsonify({
        'activities': activities,
        'stats': stats
    })

@activity_bp.route('/user/<user_id>')
def user_activities(user_id):
    """Page d'activités filtrées pour un utilisateur spécifique"""
    if not session.get('user_id'):
        flash("Vous devez être connecté pour accéder à cette page.", "warning")
        return redirect(url_for('login'))
    
    # Vérifier si l'utilisateur existe
    user = get_db("SELECT * FROM USEUR WHERE ID = ?", (user_id,))
    if not user:
        flash("Utilisateur introuvable.", "error")
        return redirect(url_for('activity_screening.index'))
    
    # Récupérer les activités de l'utilisateur
    activities = get_user_activities(user_id)
    
    return render_template('activity_screening/user_activities.html',
                          activities=activities,
                          user=user[0])

# Fonctions utilitaires
def get_recent_activities(hours=24):
    """Récupère les activités récentes des dernières X heures"""
    # Calculer la date limite
    limit_date = (datetime.now() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
    
    # Requête pour obtenir les activités avec le nom de l'utilisateur
    query = """
        SELECT al.*, u.name as user_name
        FROM activity_logs al
        LEFT JOIN USEUR u ON al.user_id = u.ID
        WHERE al.timestamp > ?
        ORDER BY al.timestamp DESC
        LIMIT 100
    """
    
    try:
        activities_data = get_db(query, (limit_date,))
        
        # Formater les données pour l'affichage
        activities = []
        for activity in activities_data:
            activities.append({
                'id': activity['id'],
                'user': activity['user_name'] or 'Système',
                'user_id': activity['user_id'],
                'action_type': activity['action_type'],
                'module': activity['module'],
                'description': activity['description'],
                'timestamp': activity['timestamp']
            })
        
        return activities
    except Exception as e:
        print(f"Erreur lors de la récupération des activités: {e}")
        return []

def get_user_activities(user_id, limit=100):
    """Récupère les activités d'un utilisateur spécifique"""
    query = """
        SELECT *
        FROM activity_logs
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
    """
    
    try:
        activities_data = get_db(query, (user_id, limit))
        
        # Formater les données pour l'affichage
        activities = []
        for activity in activities_data:
            activities.append({
                'id': activity['id'],
                'action_type': activity['action_type'],
                'module': activity['module'],
                'description': activity['description'],
                'timestamp': activity['timestamp']
            })
        
        return activities
    except Exception as e:
        print(f"Erreur lors de la récupération des activités de l'utilisateur: {e}")
        return []

def get_activity_stats():
    """Récupère les statistiques globales pour l'affichage"""
    stats = {
        'tickets_ouverts': 0,
        'tickets_resolus': 0,
        'tickets_resolus_today': 0,
        'tickets_urgents': 0,
        'temps_moyen_resolution': "00:00",
        'activites_aujourdhui': 0,
        'utilisateurs_actifs': 0
    }
    
    try:
        # Tickets ouverts
        open_tickets = get_db("SELECT COUNT(*) as count FROM tiqué WHERE open = 1")
        stats['tickets_ouverts'] = open_tickets[0]['count'] if open_tickets else 0
        
        # Tickets résolus (total)
        closed_tickets = get_db("SELECT COUNT(*) as count FROM tiqué WHERE open = 0")
        stats['tickets_resolus'] = closed_tickets[0]['count'] if closed_tickets else 0
        
        # Tickets résolus aujourd'hui
        today = datetime.now().strftime("%Y-%m-%d")
        today_tickets = get_db("SELECT COUNT(*) as count FROM tiqué WHERE open = 0 AND date_close LIKE ?", (f"{today}%",))
        stats['tickets_resolus_today'] = today_tickets[0]['count'] if today_tickets else 0
        
        # Tickets urgents
        urgent_tickets = get_db("SELECT COUNT(*) as count FROM tiqué WHERE open = 1 AND gravite <= 2")
        stats['tickets_urgents'] = urgent_tickets[0]['count'] if urgent_tickets else 0
        
        # Temps moyen de résolution
        avg_time_query = """
            SELECT AVG(julianday(date_close) - julianday(date_open)) * 24 * 60 as avg_minutes
            FROM tiqué
            WHERE open = 0 AND date_close IS NOT NULL
        """
        avg_time = get_db(avg_time_query)
        
        if avg_time and avg_time[0]['avg_minutes']:
            avg_minutes = int(avg_time[0]['avg_minutes'])
            hours = avg_minutes // 60
            minutes = avg_minutes % 60
            stats['temps_moyen_resolution'] = f"{hours:02d}:{minutes:02d}"
        
        # Nombre d'activités aujourd'hui
        today_activities = get_db("SELECT COUNT(*) as count FROM activity_logs WHERE timestamp LIKE ?", (f"{today}%",))
        stats['activites_aujourdhui'] = today_activities[0]['count'] if today_activities else 0
        
        # Nombre d'utilisateurs actifs aujourd'hui
        active_users = get_db("""
            SELECT COUNT(DISTINCT user_id) as count 
            FROM activity_logs 
            WHERE timestamp LIKE ? AND user_id IS NOT NULL
        """, (f"{today}%",))
        stats['utilisateurs_actifs'] = active_users[0]['count'] if active_users else 0
        
    except Exception as e:
        print(f"Erreur lors de la récupération des statistiques: {e}")
    
    return stats

def get_ticket_activity_data():
    """Récupère les données d'activité des tickets pour les graphiques"""
    # Structure de données attendue par le graphique
    data = {
        'labels': [],
        'created': [],
        'closed': []
    }
    
    try:
        # Récupérer les 7 derniers jours
        today = datetime.now()
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            day_str = day.strftime("%Y-%m-%d")
            label = day.strftime("%d/%m")
            
            # Tickets créés ce jour
            created = get_db(
                "SELECT COUNT(*) as count FROM tiqué WHERE date_open LIKE ?", 
                (f"{day_str}%",)
            )
            # Tickets fermés ce jour
            closed = get_db(
                "SELECT COUNT(*) as count FROM tiqué WHERE date_close LIKE ?", 
                (f"{day_str}%",)
            )
            
            data['labels'].append(label)
            data['created'].append(created[0]['count'] if created else 0)
            data['closed'].append(closed[0]['count'] if closed else 0)
    
    except Exception as e:
        print(f"Erreur lors de la récupération des données d'activité des tickets: {e}")
        # En cas d'erreur, on renvoie des données par défaut pour éviter de crasher l'application
        data = {
            'labels': [f"{i}/01" for i in range(1, 8)],
            'created': [0] * 7,
            'closed': [0] * 7
        }
    
    return data


def get_ticket_distribution_data():
    """Récupère les données de distribution des tickets pour les graphiques"""
    # Structure de données attendue par le graphique
    data = {
        'labels': ['Urgents', 'Élevés', 'Normaux', 'Faibles', 'Très faibles'],
        'data': [0, 0, 0, 0, 0]
    }
    
    try:
        # Requête pour compter les tickets par niveau de gravité
        distribution = get_db("""
            SELECT 
                SUM(CASE WHEN gravite <= 2 THEN 1 ELSE 0 END) as urgents,
                SUM(CASE WHEN gravite > 2 AND gravite <= 4 THEN 1 ELSE 0 END) as eleves,
                SUM(CASE WHEN gravite > 4 AND gravite <= 6 THEN 1 ELSE 0 END) as normaux,
                SUM(CASE WHEN gravite > 6 AND gravite <= 8 THEN 1 ELSE 0 END) as faibles,
                SUM(CASE WHEN gravite > 8 THEN 1 ELSE 0 END) as tres_faibles
            FROM tiqué 
            WHERE open = 1
        """)
        
        if distribution:
            data['data'] = [
                distribution[0]['urgents'] or 0,
                distribution[0]['eleves'] or 0,
                distribution[0]['normaux'] or 0,
                distribution[0]['faibles'] or 0,
                distribution[0]['tres_faibles'] or 0
            ]
    
    except Exception as e:
        print(f"Erreur lors de la récupération des données de distribution des tickets: {e}")
    
    return data


@activity_bp.route('/export_logs')
def export_logs():
    """Exporte les logs d'activité au format CSV"""
    if not session.get('user_id'):
        flash("Vous devez être connecté pour accéder à cette fonctionnalité.", "warning")
        return redirect(url_for('login'))
    
    # Par défaut, on exporte les 1000 dernières activités
    logs_limit = request.args.get('limit', 1000, type=int)
    
    try:
        # Requête pour obtenir les logs avec le nom de l'utilisateur
        query = """
            SELECT al.id, u.name, al.module, al.action_type, al.description, al.timestamp
            FROM activity_logs al
            LEFT JOIN USEUR u ON al.user_id = u.ID
            ORDER BY al.timestamp DESC
            LIMIT ?
        """
        
        logs_data = get_db(query, (logs_limit,))
        
        # Créer un CSV en mémoire
        csv_data = StringIO()
        csv_writer = csv.writer(csv_data)
        
        # Écrire l'en-tête
        csv_writer.writerow(['ID', 'Utilisateur', 'Module', 'Action', 'Description', 'Date'])
        
        # Écrire les données
        for log in logs_data:
            csv_writer.writerow([
                log['id'],
                log['name'] or 'Système',
                log['module'],
                log['action_type'],
                log['description'],
                log['timestamp']
            ])
        
        # Rembobiner le buffer et créer une réponse
        csv_data.seek(0)
        
        # Générer un nom de fichier avec la date actuelle
        filename = f"activity_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # Renvoyer le CSV comme pièce jointe
        return send_file(
            csv_data,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        print(f"Erreur lors de l'export des logs: {e}")
        flash(f"Erreur lors de l'export des logs: {str(e)}", "error")
        return redirect(url_for('activity_screening.index'))