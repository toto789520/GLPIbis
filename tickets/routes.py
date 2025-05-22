from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from utils.db_manager import get_db, log_activity
from onekey.user import get_user_info, list_users
from .ticket_service import (
    create_ticket, list_tickets, get_ticket_info, close_ticket, 
    associate_hardware_to_ticket, disassociate_hardware_from_ticket, 
    get_associated_hardware, get_available_hardware, SousTicketService
)
from .comment_service import CommentService
from datetime import datetime
import logging

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
    
    # Types prédéfinis au lieu d'essayer de récupérer d'une table inexistante
    software_categories = ['os', 'office', 'email', 'browser', 'antivirus', 'erp', 'other_sw']
    hardware_categories = ['desktop', 'laptop', 'printer', 'scanner', 'phone', 'peripheral', 'other_hw']
    
    return render_template('tickets/index.html', 
                          tickets=tickets, 
                          filter=filter_type,
                          software_categories=software_categories,
                          hardware_categories=hardware_categories,
                          now=datetime.now())

@tickets_bp.route('/create', methods=['GET', 'POST'])
@tickets_bp.route('/subticket/<ticket_id>/create', methods=['GET', 'POST'])
def create():
    """Création d'un nouveau ticket ou d'un sous-ticket"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    # Pour l'affichage du matériel disponible dans le formulaire
    hardware_list = get_available_hardware()
    
    if request.method == 'POST':
        titre = request.form.get('titre')
        description = request.form.get('description')
        gravite = request.form.get('gravite')
        ticket_type = request.form.get('type')
        categorie = request.form.get('categorie')
        tags = request.form.get('tags', '')
        equipement = request.form.get('equipement')
        parent_ticket_id = request.form.get('parent_ticket_id')  # For sub-tickets
        
        # Construire les tags avec le type et la catégorie
        if ticket_type and categorie:
            tags_list = [tag.strip() for tag in tags.split(',')] if tags else []
            if ticket_type not in tags_list:
                tags_list.append(ticket_type)
            if categorie not in tags_list:
                tags_list.append(categorie)
            tags = ','.join(tags_list)
        
        if not all([titre, description, gravite, ticket_type, categorie]):
            flash("Tous les champs obligatoires doivent être remplis", "error")
            return render_template('tickets/create.html', hardware_list=hardware_list, now=datetime.now())
        
        try:
            if parent_ticket_id:
                # Create a sub-ticket
                ticket_id = SousTicketService.creer_sous_ticket(
                    parent_ticket_id, titre, description, gravite, user_id, None
                )
                log_activity(user_id, 'create', 'subticket', f"Sous-ticket créé: {titre}")
            else:
                # Create a main ticket
                ticket_id = create_ticket(user_id, titre, description, gravite, tags)
                
                # Si un équipement est sélectionné, l'associer au ticket
                if equipement:
                    associate_hardware_to_ticket(ticket_id, equipement)
                    
                log_activity(user_id, 'create', 'ticket', f"Ticket créé: {titre}")
            
            flash("Le ticket a été créé avec succès!", "success")
            return redirect(url_for('tickets.view', ticket_id=ticket_id))
        except Exception as e:
            flash(f"Erreur lors de la création du ticket: {str(e)}", "error")
            return render_template('tickets/create.html', hardware_list=hardware_list, now=datetime.now())
    
    return render_template('tickets/create.html', hardware_list=hardware_list, now=datetime.now())

@tickets_bp.route('/view/<ticket_id>')
def view(ticket_id):
    """Affiche les détails d'un ticket spécifique"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    try:
        print(f"DEBUG - view: Récupération des informations du ticket {ticket_id}")
        ticket_tuple = get_ticket_info(ticket_id)
        print(f"DEBUG - view: Informations du ticket récupérées : {ticket_tuple}")
        
        if not ticket_tuple:
            flash("Ticket non trouvé", "error")
            return redirect(url_for('tickets.index'))
        
        # Convertir le tuple en dictionnaire avec des clés correspondant au template
        ticket = {
            "ID_tiqué": ticket_tuple[0],
            "ID_user": ticket_tuple[1],
            "titre": ticket_tuple[2],
            "date_open": ticket_tuple[3],
            "description": ticket_tuple[4] if ticket_tuple[4] is not None else "",
            "gravite": int(ticket_tuple[5]) if ticket_tuple[5] is not None else 0,
            "tag": ticket_tuple[6] if ticket_tuple[6] is not None else "",
            "open": ticket_tuple[7],
            "date_close": ticket_tuple[8] if len(ticket_tuple) > 8 else None,
            "user_name": ticket_tuple[9] if len(ticket_tuple) > 9 else "Utilisateur inconnu",
            "assigned_technician_id": ticket_tuple[10] if len(ticket_tuple) > 10 else None,
            "assigned_technician_name": ticket_tuple[11] if len(ticket_tuple) > 11 else None
        }
        
        print(f"DEBUG - view: Ticket formaté en dict : {ticket}")
          print(f"DEBUG - view: Récupération des commentaires du ticket {ticket_id}")
        comments = CommentService.get_comments(ticket_id)
        print(f"DEBUG - view: {len(comments)} commentaires récupérés")
        
        # Récupérer la liste des utilisateurs pour l'assignation
        users = list_users()
        
        # Calculer la date de dernière mise à jour
        last_update = ticket["date_open"]  # Par défaut, date de création
        if comments:
            # Prendre la date du commentaire le plus récent
            last_comment_date = comments[-1][1]  # Date du dernier commentaire
            last_update = last_comment_date
        
        # Remplacer les IDs utilisateurs par les noms d'utilisateurs et convertir en dict pour template
        formatted_comments = []
        for comment in comments:
            user_info = get_user_info(comment[0])
            user_name = user_info['name'] if user_info else "Utilisateur inconnu"
            # Assuming comment tuple structure: (user_id, date, hour, commenter, gravité)
            comment_dict = {
                "user_name": user_name,
                "date": comment[1],
                "hour": comment[2],
                "commenter": comment[3],
                "gravité": comment[4] if len(comment) > 4 else 0
            }
            formatted_comments.append(comment_dict)
        
        # Récupérer le matériel associé à ce ticket
        print(f"DEBUG - view: Récupération du matériel associé au ticket {ticket_id}")
        associated_hardware = get_associated_hardware(ticket_id)
        # Récupérer la liste de tout le matériel disponible
        available_hardware = get_available_hardware()
        
        # Récupérer les sous-tickets
        print(f"DEBUG - view: Récupération des sous-tickets pour le ticket {ticket_id}")
        sous_tickets = SousTicketService.get_sous_tickets(ticket_id)
        
        return render_template('tickets/view.html', 
                              ticket=ticket, 
                              comments=formatted_comments,
                              ticket_id=ticket_id,
                              associated_hardware=associated_hardware,
                              available_hardware=available_hardware,
                              creator_name=ticket["user_name"],
                              last_update=last_update,
                              users=users,
                              sous_tickets=sous_tickets,
                              now=datetime.now())
    except Exception as e:
        print(f"DEBUG - view: ERREUR lors de l'accès au ticket {ticket_id}: {str(e)}")
        import traceback
        print(f"DEBUG - view: Traceback complet: {traceback.format_exc()}")
        flash(f"Erreur lors de l'accès au ticket: {str(e)}", "error")
        return redirect(url_for('tickets.index'))

@tickets_bp.route('/subticket/<subticket_id>')
def view_subticket(subticket_id):
    """Récupère les détails d'un sous-ticket en JSON"""
    try:
        # Vérifier d'abord si la table existe
        check_query = "SELECT name FROM sqlite_master WHERE type='table' AND name='sous_tickets'"
        tables = get_db(check_query)
        
        if not tables:
            print("La table 'sous_tickets' n'existe pas encore. Création des tables requises...")
            from tickets.create_sous_tickets_tables import create_sous_tickets_tables
            create_sous_tickets_tables()
            return jsonify({'error': 'Système de sous-tickets en cours d\'initialisation, veuillez réessayer.'}), 404
        
        sous_tickets = get_db("""
            SELECT st.*, u1.name as createur_name, u2.name as assigne_name,
                   t.titre as ticket_parent_titre
            FROM sous_tickets st
            LEFT JOIN USEUR u1 ON st.createur_id = u1.ID
            LEFT JOIN USEUR u2 ON st.assigne_a = u2.ID
            LEFT JOIN tiqué t ON st.parent_ticket_id = t.ID_tiqué
            WHERE st.id = ?
        """, (subticket_id,))
        
        if not sous_tickets:
            return jsonify({'error': 'Sous-ticket non trouvé'}), 404
        
        st = sous_tickets[0]
        return jsonify({
            'id': st[0],
            'parent_ticket_id': st[1],
            'titre': st[2],
            'description': st[3],
            'statut': st[4],
            'priorite': st[5],
            'date_creation': str(st[7]),
            'date_modification': str(st[8]) if st[8] else None,
            'date_resolution': str(st[9]) if st[9] else None,
            'createur_name': st[11],
            'assigne_name': st[12],
            'ticket_parent_titre': st[13]
        })
    except Exception as e:
        print(f"Erreur lors de la récupération du sous-ticket: {e}")
        return jsonify({'error': f'Erreur lors de la récupération du sous-ticket: {str(e)}'}), 500

@tickets_bp.route('/<ticket_id>/subticket', methods=['POST'])
def add_subticket(ticket_id):
    """Crée un nouveau sous-ticket"""
    if not session.get('user_id'):
        return redirect(url_for('login'))
    
    # Vérifier d'abord si les tables de sous-tickets existent
    check_query = "SELECT name FROM sqlite_master WHERE type='table' AND name='sous_tickets'"
    tables = get_db(check_query)
    
    if not tables:
        print("La table 'sous_tickets' n'existe pas encore. Création des tables requises...")
        from tickets.create_sous_tickets_tables import create_sous_tickets_tables
        create_sous_tickets_tables()
    
    titre = request.form.get('titre')
    description = request.form.get('description')
    priorite = request.form.get('priorite', 5)
    assigne_a = request.form.get('assigne_a')
    
    try:
        sous_ticket_id = SousTicketService.creer_sous_ticket(
            ticket_id, titre, description, priorite,
            session['user_id'], assigne_a
        )
        
        if sous_ticket_id:
            flash("Sous-ticket créé avec succès", "success")
        else:
            flash("Erreur lors de la création du sous-ticket", "error")
            
    except Exception as e:
        flash(f"Erreur: {str(e)}", "error")
    
    return redirect(url_for('tickets.view', ticket_id=ticket_id))

@tickets_bp.route('/subticket/<subticket_id>/resolve', methods=['POST'])
def resolve_subticket(subticket_id):
    """Marque un sous-ticket comme résolu"""
    if not session.get('user_id'):
        return jsonify({'error': 'Non autorisé'}), 401
    
    try:
        success = SousTicketService.changer_statut(
            subticket_id, 'resolu', session['user_id']
        )
        
        if success:
            return jsonify({'status': 'success'})
        else:
            return jsonify({'error': 'Erreur lors de la résolution'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tickets_bp.route('/subticket/<subticket_id>/assign', methods=['POST'])
def assign_subticket(subticket_id):
    """Assigne un sous-ticket à un utilisateur"""
    if not session.get('user_id'):
        return jsonify({'error': 'Non autorisé'}), 401
    
    assigne_a = request.form.get('assigne_a')
    if not assigne_a:
        return jsonify({'error': 'Utilisateur non spécifié'}), 400
    
    try:
        success = SousTicketService.assigner_sous_ticket(
            subticket_id, assigne_a, session['user_id']
        )
        
        if success:
            return jsonify({'status': 'success'})
        else:
            return jsonify({'error': 'Erreur lors de l\'assignation'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tickets_bp.route('/subticket/<subticket_id>/comment', methods=['POST'])
def add_subticket_comment(subticket_id):
    """Ajoute un commentaire à un sous-ticket"""
    if not session.get('user_id'):
        return jsonify({'error': 'Non autorisé'}), 401
    
    commentaire = request.form.get('commentaire')
    if not commentaire:
        return jsonify({'error': 'Commentaire vide'}), 400
    
    try:
        success = SousTicketService.ajouter_commentaire(
            subticket_id, session['user_id'], commentaire
        )
        
        if success:
            return jsonify({'status': 'success'})
        else:
            return jsonify({'error': 'Erreur lors de l\'ajout du commentaire'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tickets_bp.route('/comment/<ticket_id>', methods=['POST'])
def comment(ticket_id):
    """Ajouter un commentaire à un ticket"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    comment_text = request.form.get('comment')
    gravite = request.form.get('gravite', '0')
    
    try:
        CommentService.add_comment(ticket_id, user_id, comment_text, gravite)
        flash("Commentaire ajouté avec succès", "success")
    except ValueError as e:
        flash(str(e), "warning")
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
    logger = logging.getLogger('glpibis')
    logger.info(f"Début de la requête de fermeture pour le ticket {ticket_id}")
    
    user_id = session.get('user_id')
    if not user_id:
        logger.warning("Tentative de fermeture de ticket sans authentification")
        return jsonify({'error': 'Vous devez être connecté pour fermer un ticket'}), 401
    
    logger.debug(f"Utilisateur {user_id} authentifié")
    
    try:
        # Vérifier d'abord si le ticket existe
        ticket = get_db("SELECT * FROM tiqué WHERE ID_tiqué = ?", (ticket_id,))
        if not ticket:
            logger.warning(f"Tentative de fermeture d'un ticket inexistant: {ticket_id}")
            return jsonify({'error': f"Le ticket {ticket_id} n'existe pas"}), 404
        
        logger.debug(f"Ticket trouvé, statut actuel: {ticket[0]}")
        
        # Appeler close_ticket
        close_ticket(ticket_id, user_id)
        
        # Vérifier que le ticket a bien été fermé
        updated_ticket = get_db("SELECT open FROM tiqué WHERE ID_tiqué = ?", (ticket_id,))
        if not updated_ticket or updated_ticket[0][0] != 0:
            logger.error(f"La fermeture du ticket {ticket_id} n'a pas été effectuée correctement")
            return jsonify({'error': 'La fermeture du ticket a échoué'}), 500
            
        logger.info(f"Ticket {ticket_id} fermé avec succès")
        
        # Enregistrer l'activité
        log_activity(user_id, 'close', 'ticket', f"Ticket {ticket_id} fermé")
        
        return jsonify({
            'success': True,
            'message': 'Le ticket a été fermé avec succès'
        })
        
    except ValueError as e:
        logger.warning(f"Erreur de validation lors de la fermeture du ticket {ticket_id}: {str(e)}")
        return jsonify({'error': str(e)}), 400
        
    except Exception as e:
        logger.exception(f"Erreur inattendue lors de la fermeture du ticket {ticket_id}")
        return jsonify({'error': 'Une erreur est survenue lors de la fermeture du ticket'}), 500

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
                # Mettre à jour le ticket dans la base de données avec des requêtes préparées
                conn = get_db('connect')
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE tiqué
                    SET titre = ?, description = ?, gravite = ?, tag = ?
                    WHERE ID_tiqué = ?
                """, (titre, description, int(gravite), tags, ticket_id))
                conn.commit()
                
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
            SET ID_technicien = ?
            WHERE ID_tiqué = ?
        """, (assigned_user_id, ticket_id))
        conn.commit()
        
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
            SET open = 1,
                date_close = NULL
            WHERE ID_tiqué = ?
        """, (ticket_id,))
        conn.commit()
        
        log_activity(user_id, 'reopen', 'ticket', f"Ticket {ticket_id} réouvert")
        flash("Le ticket a été réouvert avec succès", "success")
    except Exception as e:
        flash(f"Erreur lors de la réouverture du ticket: {str(e)}", "error")
    
    return redirect(url_for('tickets.view', ticket_id=ticket_id))

@tickets_bp.route('/comment/<comment_id>/delete', methods=['POST'])
def delete_comment(comment_id):
    """Supprimer un commentaire"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
        
    try:
        CommentService.delete_comment(comment_id, user_id)
        flash("Commentaire supprimé avec succès", "success")
    except ValueError as e:
        flash(str(e), "warning")
    except Exception as e:
        flash(f"Erreur lors de la suppression: {str(e)}", "error")
        
    return redirect(request.referrer or url_for('tickets.index'))
    
@tickets_bp.route('/comment/<comment_id>/edit', methods=['POST'])
def edit_comment(comment_id):
    """Modifier un commentaire"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
        
    content = request.form.get('content')
    gravite = request.form.get('gravite')
    
    try:
        CommentService.update_comment(comment_id, user_id, content, gravite)
        flash("Commentaire modifié avec succès", "success")
    except ValueError as e:
        flash(str(e), "warning")
    except Exception as e:
        flash(f"Erreur lors de la modification: {str(e)}", "error")
        
    return redirect(request.referrer or url_for('tickets.index'))