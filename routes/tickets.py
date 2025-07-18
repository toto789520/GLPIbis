from hmac import new
from operator import eq
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
import app
from onekey.auth import validate_session
from onekey.user import get_user_info
from utils.db_manager import get_db
from utils.logger import get_logger
from inventory.inventory_service import InventoryService
from datetime import datetime
from tickets.ticket_service import get_ticket_info, create_ticket as service_create_ticket, close_ticket, get_ticket_list

tickets_bp = Blueprint('tickets', __name__, url_prefix='/tickets')
logger = get_logger()

@tickets_bp.route('/')
def index():
    """Affichage de la liste des tickets"""
    try:
        tickets = get_ticket_list()
        logger.debug(f"DEBUG - index: Récupération de la liste des tickets: {tickets}")
        count = len(tickets) if tickets else 0
        logger.debug(f"DEBUG - index: {count} tickets récupérés")
        
        return render_template('tickets/index.html', tickets=tickets or [], now=datetime.now())
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des tickets: {str(e)}")
        flash("Erreur lors du chargement des tickets", "error")
        return render_template('tickets/index.html', tickets=[], now=datetime.now())

@tickets_bp.route('/view/<int:ticket_id>')
def view(ticket_id):
    """Affichage d'un ticket spécifique"""    
    try:
        logger.debug(f"DEBUG - view: Récupération des informations du ticket {ticket_id}")
        ticket_data = get_ticket_info(ticket_id)
            
        logger.debug(f"DEBUG - view: Informations récupérées de la db: {ticket_data}")
        if not ticket_data:
            logger.debug(f"DEBUG - view: Ticket {ticket_id} non trouvé")
            flash("Ticket non trouvé", "error")
            return redirect(url_for('tickets.index'))
        
        comments = get_db("""
            SELECT tc.*, u.name 
            FROM ticket_comments tc
            LEFT JOIN USEUR u ON tc.ID_user = u.ID
            WHERE tc.ticket_id = ?
            ORDER BY tc.created_at DESC
        """, (ticket_id,)) or []
        
        return render_template('tickets/view.html', 
                             ticket=ticket_data, 
                             comments=comments,
                             now=datetime.now())
    except Exception as e:
        logger.error(f"Erreur lors de l'accès au ticket {ticket_id}: {str(e)}")
        flash("Erreur lors de l'accès au ticket", "error")
        return redirect(url_for('tickets.index'))

@tickets_bp.route('/create', methods=['GET', 'POST'])
def create_ticket_route():
    """Création d'un nouveau ticket"""
    if not session.get('user_id'):
        flash("Vous devez être connecté pour créer un ticket", "error")
        return redirect(url_for('login'))

    if request.method == 'POST':
        logger.debug("DEBUG - create_ticket: Traitement du formulaire de création de ticket")
        try:
            # Validation améliorée
            titre = request.form.get('titre', '').strip()
            if len(titre) < 3:
                logger.debug("DEBUG - create_ticket: Titre invalide")
                raise ValueError("Le titre doit contenir au moins 3 caractères")

            description = request.form.get('description', '').strip()
            if len(description) < 10:
                logger.debug("DEBUG - create_ticket: Description invalide")
                raise ValueError("La description doit être plus détaillée")
            
            # Récupération des Informations du formulaire
            logger.debug("DEBUG - create_ticket: Récupération des informations du formulaire")
            gravite = request.form.get('gravite', '3')
            tags = request.form.get('tags', '').strip()
            equipment_id = request.form.get('equipement_id')
            new_equipement = request.form.get('new_equipement', '0') == '1'
            categorie = request.form.get('categorie', '').strip()
            user_id = session.get('user_id')
            new_ticket_id = service_create_ticket(user_id, titre, description, gravite, tags, equipment_id, new_equipement, categorie)
            logger.debug(f"DEBUG - create_ticket: Ticket créé avec succès: {new_ticket_id}")
            flash("Ticket créé avec succès", "success")
            return redirect(url_for('tickets.view', ticket_id=new_ticket_id))
        except ValueError as ve:
            flash(str(ve), "error")
            return render_template('tickets/create.html')
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
        logger.error(f"Erreur lors de la fermeture du ticket: {e}")
        flash("Erreur lors de la fermeture du ticket", "error")
        return redirect(url_for('tickets.view', ticket_id=ticket_id))
