from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from onekey.auth import validate_session
from utils.db_manager import get_db
from utils.logger import get_logger
from datetime import datetime

tickets_bp = Blueprint('tickets', __name__, url_prefix='/tickets')
logger = get_logger()

@tickets_bp.route('/')
def index():
    """Affichage de la liste des tickets"""
    try:
        # Correction du nom de table et requête plus robuste
        tickets = get_db("SELECT * FROM tiqué ORDER BY date_open DESC")
        if tickets is None:
            tickets = []
        
        count = len(tickets) if isinstance(tickets, (list, tuple)) else 0
        logger.debug(f"DEBUG - index: {count} tickets récupérés")
        return render_template('tickets/index.html', tickets=tickets, now=datetime.now())
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des tickets: {e}")
        flash("Erreur lors du chargement des tickets", "error")
        return render_template('tickets/index.html', tickets=[], now=datetime.now())

@tickets_bp.route('/view/<int:ticket_id>')
def view(ticket_id):
    """Affichage d'un ticket spécifique"""    
    try:
        logger.debug(f"DEBUG - view: Récupération des informations du ticket {ticket_id}")
        from tickets.ticket_service import get_ticket_info
        ticket = get_ticket_info(ticket_id)
            
        logger.debug(f"DEBUG - view: Informations récupérées de la db: {ticket}")
        logger.debug(f"DEBUG - view: Ticket trouvé: {ticket is not None}")
        if not ticket:
            flash("Ticket non trouvé", "error")
            return redirect(url_for('tickets.index'))
        return render_template('tickets/view.html', ticket=ticket, now=datetime.now())
    except Exception as e:
        logger.debug(f"DEBUG - view: ERREUR lors de l'accès au ticket {ticket_id}: {e}")
        flash("Erreur lors de l'accès au ticket", "error")
        return redirect(url_for('tickets.index'))

@tickets_bp.route('/create', methods=['GET', 'POST'])
def create_ticket():
    """Création d'un nouveau ticket"""
    if request.method == 'POST':
        try:
            from flask import session
            from tickets.ticket_service import create_ticket as service_create_ticket
            
            # Vérifier que l'utilisateur est connecté
            if 'user_id' not in session:
                flash("Vous devez être connecté pour créer un ticket", "error")
                return redirect(url_for('login'))
            
            # Récupérer les données du formulaire
            titre = request.form.get('titre')
            description = request.form.get('description')
            gravite = request.form.get('gravite', 3)
            tags = request.form.get('tags', '')
            
            # Validation des champs obligatoires
            if not titre or not description:
                flash("Le titre et la description sont obligatoires", "error")
                return render_template('tickets/create.html', now=datetime.now())
            
            # Créer le ticket via le service
            ticket_id = service_create_ticket(
                user_id=session['user_id'],
                titre=titre,
                description=description,
                gravite=int(gravite),
                tags=tags
            )
            
            logger.info(f"Ticket {ticket_id} créé avec succès par l'utilisateur {session['user_id']}")
            flash(f"Ticket #{ticket_id} créé avec succès", "success")
            return redirect(url_for('tickets.view', ticket_id=ticket_id))
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du ticket: {e}")
            flash("Erreur lors de la création du ticket", "error")
    
    # Récupérer la liste des équipements pour le formulaire
    try:
        hardware_list = get_db("SELECT id, name, category FROM inventory ORDER BY name")
    except Exception:
        hardware_list = []
    
    return render_template('tickets/create.html', now=datetime.now(), hardware_list=hardware_list)

@tickets_bp.route('/update/<int:ticket_id>', methods=['GET', 'POST'])
def update(ticket_id):
    """Mise à jour d'un ticket"""
    try:
        from tickets.ticket_service import get_ticket_info
        from flask import session
        
        # Récupérer le ticket
        ticket = get_ticket_info(ticket_id)
        if not ticket:
            flash("Ticket non trouvé", "error")
            return redirect(url_for('tickets.index'))
        
        if request.method == 'POST':
            # Récupérer les données du formulaire
            assigned_user_id = request.form.get('assigned_user_id')
            titre = request.form.get('titre')
            description = request.form.get('description')
            gravite = request.form.get('gravite')
            tags = request.form.get('tags')
            
            # Construire la requête de mise à jour
            if assigned_user_id is not None:
                get_db("""
                    UPDATE tiqué 
                    SET ID_technicien = ?
                    WHERE ID_tiqué = ?
                """, (assigned_user_id if assigned_user_id else None, ticket_id))
                flash("Ticket assigné avec succès", "success")
            
            if titre or description or gravite or tags:
                # Mise à jour des champs du ticket
                update_fields = []
                params = []
                
                if titre:
                    update_fields.append("titre = ?")
                    params.append(titre)
                if description:
                    update_fields.append("description = ?")
                    params.append(description)
                if gravite:
                    update_fields.append("gravite = ?")
                    params.append(int(gravite))
                if tags is not None:
                    update_fields.append("tag = ?")
                    params.append(tags)
                
                if update_fields:
                    params.append(ticket_id)
                    query = f"UPDATE tiqué SET {', '.join(update_fields)} WHERE ID_tiqué = ?"
                    get_db(query, tuple(params))
                    flash("Ticket mis à jour avec succès", "success")
            
            return redirect(url_for('tickets.view', ticket_id=ticket_id))
        
        # GET: Afficher le formulaire de modification
        return render_template('tickets/update.html', ticket=ticket, now=datetime.now())
        
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour du ticket: {e}")
        flash("Erreur lors de la mise à jour", "error")
        return redirect(url_for('tickets.view', ticket_id=ticket_id))

@tickets_bp.route('/filter/<filter_type>')
def filter_tickets(filter_type):
    """Filtrage des tickets"""
    try:
        # Utiliser get_db avec des requêtes SQL directes
        if filter_type == 'open':
            tickets = get_db("SELECT * FROM tiqué WHERE open = 1")
        elif filter_type == 'closed':
            tickets = get_db("SELECT * FROM tiqué WHERE open = 0")
        else:
            tickets = get_db("SELECT * FROM tiqué")
        
        return render_template('tickets/index.html', tickets=tickets or [], now=datetime.now())
    except Exception as e:
        logger.error(f"Erreur lors du filtrage des tickets: {e}")
        flash("Erreur lors du filtrage des tickets", "error")
        return redirect(url_for('tickets.index'))

@tickets_bp.route('/close/<int:ticket_id>', methods=['POST'])
def close_ticket(ticket_id):
    """Fermeture d'un ticket"""
    try:
        from tickets.ticket_service import close_ticket as service_close_ticket
        user_id = request.form.get('user_id')  # Optionnel
        service_close_ticket(ticket_id, user_id)
        flash("Ticket fermé avec succès", "success")
        return redirect(url_for('tickets.view', ticket_id=ticket_id))
    except Exception as e:
        logger.error(f"Erreur lors de la fermeture du ticket: {e}")
        flash("Erreur lors de la fermeture du ticket", "error")
        return redirect(url_for('tickets.view', ticket_id=ticket_id))
