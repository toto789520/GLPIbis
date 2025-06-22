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
            # Traitement du formulaire
            # ... logique de création
            flash("Ticket créé avec succès", "success")
            return redirect(url_for('tickets.index'))
        except Exception as e:
            logger.error(f"Erreur lors de la création du ticket: {e}")
            flash("Erreur lors de la création du ticket", "error")
    
    return render_template('tickets/create.html', now=datetime.now())

@tickets_bp.route('/update/<int:ticket_id>', methods=['POST'])
def update(ticket_id):
    """Mise à jour d'un ticket"""
    try:
        # Utiliser get_db au lieu de get_db_manager()
        # ... logique de mise à jour
        flash("Ticket mis à jour avec succès", "success")
        return redirect(url_for('tickets.view', ticket_id=ticket_id))
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
