from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from utils.db import get_db, log_activity
from onekey.user import get_user_info
from .ticket_service import (
    create_ticket, list_tickets, get_ticket_info, get_ticket_comments, 
    add_comment as add_ticket_comment,  # Renommer l'import pour éviter le conflit
    close_ticket, associate_hardware_to_ticket, 
    disassociate_hardware_from_ticket, get_associated_hardware, get_available_hardware
)
from datetime import datetime

# Création du Blueprint pour les routes liées aux tickets
tickets_bp = Blueprint('tickets', __name__, template_folder='templates')

@tickets_bp.route('/')
def index():
    """Liste tous les tickets disponibles pour l'utilisateur"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    # Filtrer les tickets selon le paramètre
    filter_type = request.args.get('filter', 'all')
    tickets = list_tickets(filter_type)
    
    # Récupérer les types de tickets et matériels pour le filtrage
    ticket_types = get_db("SELECT * FROM tiqué_type")
    hardware_types = get_db("SELECT * FROM arder")
    
    # Formatter les noms pour le filtrage (remplacer les espaces par des underscores)
    software_categories = [t[0].replace(" ", "_") for t in ticket_types] if ticket_types else []
    hardware_categories = [h[0].replace(" ", "_") for h in hardware_types] if hardware_types else []
    
    return render_template('tickets/index.html', 
                          tickets=tickets, 
                          filter=filter_type,
                          software_categories=software_categories,
                          hardware_categories=hardware_categories,
                          now=datetime.now())

@tickets_bp.route('/create', methods=['GET', 'POST'])
def create():
    """Création d'un nouveau ticket"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        titre = request.form.get('titre')
        description = request.form.get('description')
        gravite = request.form.get('gravite')
        tags = request.form.get('tags')
        
        if not all([titre, description, gravite]):
            flash("Tous les champs obligatoires doivent être remplis", "error")
            return render_template('tickets/create.html', now=datetime.now())
        
        try:
            ticket_id = create_ticket(user_id, titre, description, gravite, tags)
            log_activity(user_id, 'create', 'ticket', f"Ticket créé: {titre}")
            flash("Le ticket a été créé avec succès!", "success")
            return redirect(url_for('tickets.view', ticket_id=ticket_id))
        except Exception as e:
            flash(f"Erreur lors de la création du ticket: {str(e)}", "error")
            return render_template('tickets/create.html', now=datetime.now())
    
    return render_template('tickets/create.html', now=datetime.now())

@tickets_bp.route('/view/<ticket_id>')
def view(ticket_id):
    """Affiche les détails d'un ticket spécifique"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    try:
        ticket = get_ticket_info(ticket_id)
        comments = get_ticket_comments(ticket_id)
        
        # Récupérer le nom de l'utilisateur qui a créé le ticket
        creator_name = ticket[-1] if ticket else "Utilisateur inconnu"  # Le nom est ajouté à la fin du tuple par get_ticket_info
        
        # Récupérer la liste des utilisateurs pour l'assignation
        users = get_db("SELECT ID, name FROM USEUR WHERE active = 1")
        
        # Calculer la date de dernière mise à jour
        last_update = ticket[2]  # Par défaut, date de création
        if comments:
            # Prendre la date du commentaire le plus récent
            last_comment_date = comments[-1][1]  # Date du dernier commentaire
            last_update = last_comment_date
        
        # Remplacer les IDs utilisateurs par les noms d'utilisateurs
        formatted_comments = []
        for comment in comments:
            user_name = get_user_info(comment[0])['name'] if get_user_info(comment[0]) else "Utilisateur inconnu"
            comment_data = list(comment)
            comment_data[0] = user_name
            formatted_comments.append(tuple(comment_data))
        
        # Récupérer le matériel associé à ce ticket
        associated_hardware = get_associated_hardware(ticket_id)
        # Récupérer la liste de tout le matériel disponible
        available_hardware = get_available_hardware()
        
        return render_template('tickets/view.html', 
                              ticket=ticket, 
                              comments=formatted_comments,
                              ticket_id=ticket_id,
                              associated_hardware=associated_hardware,
                              available_hardware=available_hardware,
                              creator_name=creator_name,
                              last_update=last_update,
                              users=users,
                              now=datetime.now())
    except Exception as e:
        flash(f"Erreur lors de l'accès au ticket: {str(e)}", "error")
        return redirect(url_for('tickets.index'))

@tickets_bp.route('/comment/<ticket_id>', methods=['POST'])
def comment(ticket_id):
    """Ajouter un commentaire à un ticket"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    comment_text = request.form.get('comment')
    gravite = request.form.get('gravite', '0')  # Par défaut, gravité 0 si non fournie
    
    if not comment_text:
        flash("Le commentaire ne peut pas être vide", "error")
        return redirect(url_for('tickets.view', ticket_id=ticket_id))
    
    try:
        add_ticket_comment(ticket_id, user_id, comment_text, gravite)  # Utiliser le nom renommé
        log_activity(user_id, 'comment', 'ticket', f"Commentaire ajouté au ticket {ticket_id}")
        flash("Commentaire ajouté avec succès", "success")
    except Exception as e:
        flash(f"Erreur lors de l'ajout du commentaire: {str(e)}", "error")
    
    return redirect(url_for('tickets.view', ticket_id=ticket_id))

@tickets_bp.route('/add_comment/<ticket_id>', methods=['POST'])
def add_comment(ticket_id):
    """Alias pour la route comment - pour compatibilité"""
    return comment(ticket_id)

@tickets_bp.route('/close/<ticket_id>', methods=['POST'])
def close(ticket_id):
    """Fermer un ticket"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    try:
        close_ticket(ticket_id, user_id)
        log_activity(user_id, 'close', 'ticket', f"Ticket {ticket_id} fermé")
        flash("Le ticket a été fermé avec succès", "success")
    except Exception as e:
        flash(f"Erreur lors de la fermeture du ticket: {str(e)}", "error")
    
    return redirect(url_for('tickets.view', ticket_id=ticket_id))

@tickets_bp.route('/api/tickets', methods=['GET'])
def api_tickets():
    """API pour récupérer la liste des tickets (utilisé par d'autres modules)"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Non autorisé'}), 401
    
    filter_type = request.args.get('filter', 'all')
    tickets = list_tickets(filter_type)
    
    return jsonify({'tickets': tickets})

@tickets_bp.route('/filter/<filter_type>')
def filter_tickets(filter_type):
    """Filtrer les tickets par type"""
    return redirect(url_for('tickets.index', filter=filter_type))

@tickets_bp.route('/hardware/associate/<ticket_id>', methods=['POST'])
def associate_hardware(ticket_id):
    """Associer du matériel à un ticket"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    hardware_id = request.form.get('hardware_id')
    if not hardware_id:
        flash("ID de matériel non fourni", "error")
        return redirect(url_for('tickets.view', ticket_id=ticket_id))
    
    try:
        associate_hardware_to_ticket(ticket_id, hardware_id)
        log_activity(user_id, 'associate', 'hardware', f"Matériel {hardware_id} associé au ticket {ticket_id}")
        flash("Matériel associé avec succès au ticket", "success")
    except Exception as e:
        flash(f"Erreur lors de l'association du matériel: {str(e)}", "error")
    
    return redirect(url_for('tickets.view', ticket_id=ticket_id))

@tickets_bp.route('/hardware/disassociate/<ticket_id>', methods=['POST'])
def disassociate_hardware(ticket_id):
    """Dissocier du matériel d'un ticket"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    hardware_id = request.form.get('hardware_id')
    if not hardware_id:
        flash("ID de matériel non fourni", "error")
        return redirect(url_for('tickets.view', ticket_id=ticket_id))
    
    try:
        disassociate_hardware_from_ticket(ticket_id, hardware_id)
        log_activity(user_id, 'disassociate', 'hardware', f"Matériel {hardware_id} dissocié du ticket {ticket_id}")
        flash("Matériel dissocié avec succès du ticket", "success")
    except Exception as e:
        flash(f"Erreur lors de la dissociation du matériel: {str(e)}", "error")
    
    return redirect(url_for('tickets.view', ticket_id=ticket_id))

@tickets_bp.route('/hardware/associate/batch/<ticket_id>', methods=['POST'])
def associate_hardware_batch(ticket_id):
    """Associer plusieurs matériels à un ticket en une seule fois"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    hardware_ids = request.form.getlist('hardware_ids')
    if not hardware_ids:
        flash("Aucun matériel sélectionné", "error")
        return redirect(url_for('tickets.view', ticket_id=ticket_id))
    
    try:
        for hardware_id in hardware_ids:
            associate_hardware_to_ticket(ticket_id, hardware_id)
        
        log_activity(user_id, 'associate_batch', 'hardware', f"{len(hardware_ids)} matériels associés au ticket {ticket_id}")
        flash(f"{len(hardware_ids)} matériels associés avec succès au ticket", "success")
    except Exception as e:
        flash(f"Erreur lors de l'association des matériels: {str(e)}", "error")
    
    return redirect(url_for('tickets.view', ticket_id=ticket_id))

@tickets_bp.route('/api/hardware/<ticket_id>', methods=['GET'])
def api_ticket_hardware(ticket_id):
    """API pour récupérer le matériel associé à un ticket"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Non autorisé'}), 401
    
    try:
        associated_hardware = get_associated_hardware(ticket_id)
        return jsonify({'hardware': associated_hardware})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tickets_bp.route('/update/<ticket_id>', methods=['GET', 'POST'])
def update(ticket_id):
    """Mettre à jour un ticket existant"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    try:
        ticket = get_ticket_info(ticket_id)
        
        if request.method == 'POST':
            titre = request.form.get('titre')
            description = request.form.get('description')
            gravite = request.form.get('gravite')
            tags = request.form.get('tags')
            
            if not all([titre, description, gravite]):
                flash("Tous les champs obligatoires doivent être remplis", "error")
                return render_template('tickets/update.html', ticket=ticket, ticket_id=ticket_id, now=datetime.now())
            
            try:
                # Mettre à jour le ticket dans la base de données
                conn = get_db('connect')
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE tiqué
                    SET titre = ?, description = ?, gravite = ?, tags = ?
                    WHERE ticket_id = ?
                """, (titre, description, gravite, tags, ticket_id))
                conn.commit()
                conn.close()
                
                log_activity(user_id, 'update', 'ticket', f"Ticket {ticket_id} mis à jour")
                flash("Le ticket a été mis à jour avec succès!", "success")
                return redirect(url_for('tickets.view', ticket_id=ticket_id))
            except Exception as e:
                flash(f"Erreur lors de la mise à jour du ticket: {str(e)}", "error")
                return render_template('tickets/update.html', ticket=ticket, ticket_id=ticket_id, now=datetime.now())
        
        return render_template('tickets/update.html', ticket=ticket, ticket_id=ticket_id, now=datetime.now())
    except Exception as e:
        flash(f"Erreur lors de l'accès au ticket: {str(e)}", "error")
        return redirect(url_for('tickets.index'))

@tickets_bp.route('/assign/<ticket_id>', methods=['POST'])
def assign(ticket_id):
    """Assigner un ticket à un utilisateur"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    assigned_user_id = request.form.get('assigned_user_id')
    if not assigned_user_id:
        flash("ID d'utilisateur non fourni", "error")
        return redirect(url_for('tickets.view', ticket_id=ticket_id))
    
    try:
        # Mettre à jour le ticket dans la base de données pour l'assigner à l'utilisateur
        conn = get_db('connect')
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE tiqué
            SET assigned_user_id = ?
            WHERE ticket_id = ?
        """, (assigned_user_id, ticket_id))
        conn.commit()
        conn.close()
        
        log_activity(user_id, 'assign', 'ticket', f"Ticket {ticket_id} assigné à l'utilisateur {assigned_user_id}")
        flash("Le ticket a été assigné avec succès", "success")
    except Exception as e:
        flash(f"Erreur lors de l'assignation du ticket: {str(e)}", "error")
    
    return redirect(url_for('tickets.view', ticket_id=ticket_id))

@tickets_bp.route('/reopen/<ticket_id>', methods=['POST'])
def reopen(ticket_id):
    """Réouvrir un ticket fermé"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    try:
        # Mettre à jour le statut du ticket dans la base de données
        conn = get_db('connect')
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE tiqué
            SET status = 0
            WHERE ticket_id = ?
        """, (ticket_id,))
        conn.commit()
        conn.close()
        
        log_activity(user_id, 'reopen', 'ticket', f"Ticket {ticket_id} réouvert")
        flash("Le ticket a été réouvert avec succès", "success")
    except Exception as e:
        flash(f"Erreur lors de la réouverture du ticket: {str(e)}", "error")
    
    return redirect(url_for('tickets.view', ticket_id=ticket_id))