from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from utils.db_manager import get_db, log_activity
from datetime import datetime
import logging

app_logger = logging.getLogger("glpibis")

tickets_bp = Blueprint('tickets', __name__, url_prefix='/tickets')

@tickets_bp.route('/')
def index():
    """Page d'accueil des tickets"""
    try:
        # Récupérer tous les tickets
        tickets = get_db("""
            SELECT t.ID_tiqué, t.ID_user, t.titre, t.date_open, 
                   COALESCE(u2.name, 'Non assigné') as assigne_a,
                   t.open, t.gravite, t.tag, t.description, t.date_close,
                   u1.name as user_name
            FROM tiqué t
            LEFT JOIN USEUR u1 ON t.ID_user = u1.ID
            LEFT JOIN USEUR u2 ON t.ID_technicien = u2.ID
            ORDER BY t.date_open DESC
        """)
        
        app_logger.debug(f"DEBUG - index: Requête SQL exécutée")
        app_logger.debug(f"DEBUG - index: Résultat brut: {tickets}")
        app_logger.debug(f"DEBUG - index: Type du résultat: {type(tickets)}")
        app_logger.debug(f"DEBUG - index: {len(tickets) if tickets else 0} tickets récupérés")
        
        # Vérifier s'il y a des tickets dans la table
        count_result = get_db("SELECT COUNT(*) FROM tiqué")
        app_logger.debug(f"DEBUG - index: Nombre total de tickets dans la table: {count_result}")
        
        return render_template('tickets/index.html', tickets=tickets or [])
        
    except Exception as e:
        app_logger.error(f"Erreur lors de la récupération des tickets: {str(e)}")
        flash("Erreur lors du chargement des tickets", "error")
        return render_template('tickets/index.html', tickets=[])

@tickets_bp.route('/filter/<filter_type>')
def filter_tickets(filter_type):
    """Filtrer les tickets selon différents critères"""
    try:
        base_query = """
            SELECT t.ID_tiqué, t.ID_user, t.titre, t.date_open, 
                   COALESCE(u2.name, 'Non assigné') as assigne_a,
                   t.open, t.gravite, t.tag, t.description, t.date_close,
                   u1.name as user_name
            FROM tiqué t
            LEFT JOIN USEUR u1 ON t.ID_user = u1.ID
            LEFT JOIN USEUR u2 ON t.ID_technicien = u2.ID
        """
        
        where_clause = ""
        params = []
        
        if filter_type == 'all':
            where_clause = ""
        elif filter_type == 'open':
            where_clause = "WHERE t.open = 1"
        elif filter_type == 'closed':
            where_clause = "WHERE t.open = 0"
        elif filter_type == 'my':
            where_clause = "WHERE t.ID_user = ?"
            params = [session.get('user_id')]
        elif filter_type.startswith('gravity_'):
            gravity = filter_type.split('_')[1]
            where_clause = "WHERE t.gravite = ?"
            params = [int(gravity)]
        elif filter_type.startswith('software_'):
            category = filter_type.replace('software_', '').replace('_', ' ')
            where_clause = "WHERE t.tag LIKE ?"
            params = [f"%{category}%"]
        elif filter_type.startswith('hardware_'):
            category = filter_type.replace('hardware_', '').replace('_', ' ')
            where_clause = "WHERE t.tag LIKE ?"
            params = [f"%{category}%"]
        
        query = f"{base_query} {where_clause} ORDER BY t.date_open DESC"
        tickets = get_db(query, params)
        
        return render_template('tickets/index.html', tickets=tickets or [], filter=filter_type)
        
    except Exception as e:
        app_logger.error(f"Erreur lors du filtrage des tickets: {str(e)}")
        flash("Erreur lors du filtrage des tickets", "error")
        return redirect(url_for('tickets.index'))

@tickets_bp.route('/create', methods=['GET', 'POST'])
def create_ticket():
    """Créer un nouveau ticket"""
    if request.method == 'POST':
        try:
            titre = request.form.get('titre')
            description = request.form.get('description')
            gravite = request.form.get('gravite', 3)
            tags = request.form.get('tags', '')
            assigned_to = request.form.get('assigned_to')
            
            app_logger.debug(f"DEBUG - create_ticket: Données reçues - titre: {titre}, description: {description[:50]}..., gravite: {gravite}")
            
            if not titre or not description:
                flash("Le titre et la description sont obligatoires", "error")
                app_logger.warning("Tentative de création de ticket avec des champs manquants")
                return render_template('tickets/create.html')
            
            # Vérifier que l'utilisateur est connecté
            user_id = session.get('user_id')
            if not user_id:
                flash("Vous devez être connecté pour créer un ticket", "error")
                return redirect(url_for('login'))
            
            # Créer le ticket
            result = get_db("""
                INSERT INTO tiqué (ID_user, titre, description, gravite, tag, date_open, open, ID_technicien)
                VALUES (?, ?, ?, ?, ?, ?, 1, ?)
            """, (user_id, titre, description, int(gravite), tags, 
                  datetime.now().strftime("%Y-%m-%d %H:%M:%S"), assigned_to if assigned_to else None))
            
            app_logger.info(f"Ticket créé avec succès pour l'utilisateur {user_id}: {titre}")
            
            # Log de l'activité
            try:
                log_activity(user_id, 'create', 'ticket', f'Ticket créé: {titre}')
            except Exception as e:
                app_logger.warning(f"Impossible de logger l'activité: {e}")
            
            flash(f"Ticket '{titre}' créé avec succès", "success")
            return redirect(url_for('tickets.index'))
            
        except Exception as e:
            app_logger.error(f"Erreur lors de la création du ticket: {str(e)}")
            flash("Erreur lors de la création du ticket", "error")
            return render_template('tickets/create.html')
    
    # GET - Afficher le formulaire
    try:
        # Récupérer la liste des utilisateurs pour l'assignation
        users = get_db("SELECT ID, name FROM USEUR ORDER BY name")
        
        # Récupérer la liste du matériel pour l'association
        hardware_list = get_db("SELECT id, nom, type FROM hardware ORDER BY nom LIMIT 100")
        
        return render_template('tickets/create.html', users=users or [], hardware_list=hardware_list or [])
    except Exception as e:
        app_logger.error(f"Erreur lors du chargement du formulaire de création: {str(e)}")
        return render_template('tickets/create.html', users=[], hardware_list=[])

@tickets_bp.route('/view/<int:ticket_id>')
def view(ticket_id):
    """Voir les détails d'un ticket"""
    try:
        app_logger.debug(f"DEBUG - view: Récupération des informations du ticket {ticket_id}")
        
        # Récupérer le ticket avec toutes les informations nécessaires
        ticket_rows = get_db("""
            SELECT t.ID_tiqué, t.ID_user, t.titre, t.date_open, t.date_close,
                   t.ID_technicien, t.description, t.open, t.tag, t.gravite,
                   u1.name as demandeur, u2.name as assigne_a
            FROM tiqué t
            LEFT JOIN USEUR u1 ON t.ID_user = u1.ID
            LEFT JOIN USEUR u2 ON t.ID_technicien = u2.ID
            WHERE t.ID_tiqué = ?
        """, (ticket_id,))

        app_logger.debug(f"DEBUG - view: Résultat de la requête pour le ticket {ticket_id}: {ticket_rows}")

        if not ticket_rows:
            app_logger.warning(f"Ticket {ticket_id} non trouvé")
            flash("Ticket non trouvé", "error")
            return redirect(url_for('tickets.index'))

        # Vérifier que ticket_rows est une liste/tuple et contient des données
        if not isinstance(ticket_rows, (list, tuple)) or len(ticket_rows) == 0:
            app_logger.error("Format de résultat inattendu de la base de données")
            flash("Erreur lors du chargement du ticket", "error")
            return redirect(url_for('tickets.index'))

        ticket = ticket_rows[0]  # Premier résultat
        
        # Créer le dictionnaire avec des valeurs par défaut sécurisées
        ticket_data = {
            'ID_tiqué': ticket[0] if len(ticket) > 0 else None,
            'ID_user': ticket[1] if len(ticket) > 1 else None,
            'titre': ticket[2] if len(ticket) > 2 else '',
            'date_open': ticket[3] if len(ticket) > 3 else None,
            'date_close': ticket[4] if len(ticket) > 4 else None,
            'ID_technicien': ticket[5] if len(ticket) > 5 else None,
            'description': ticket[6] if len(ticket) > 6 else '',
            'open': ticket[7] if len(ticket) > 7 else True,
            'tag': ticket[8] if len(ticket) > 8 else '',
            'gravite': ticket[9] if len(ticket) > 9 else 3,  # Valeur par défaut de 3
        }
        
        app_logger.debug(f"Ticket {ticket_id} chargé avec succès")
        return render_template('tickets/view.html', ticket=ticket_data, now=datetime.now())
        
    except Exception as e:
        app_logger.debug(f"DEBUG - view: ERREUR lors de l'accès au ticket {ticket_id}: {str(e)}")
        flash("Erreur lors du chargement du ticket", "error")
        return redirect(url_for('tickets.index'))

@tickets_bp.route('/close/<int:ticket_id>', methods=['POST'])
def close_ticket(ticket_id):
    """Fermer un ticket"""
    try:
        # Mettre à jour le ticket
        get_db("""
            UPDATE tiqué 
            SET open = 0, date_close = ? 
            WHERE ID_tiqué = ?
        """, (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), ticket_id))
        
        # Log de l'activité
        try:
            log_activity(session.get('user_id'), 'close', 'ticket', f'Ticket {ticket_id} fermé')
        except:
            pass
        
        flash("Ticket fermé avec succès", "success")
        return redirect(url_for('tickets.view', ticket_id=ticket_id))
        
    except Exception as e:
        app_logger.error(f"Erreur lors de la fermeture du ticket: {str(e)}")
        flash("Erreur lors de la fermeture du ticket", "error")
        return redirect(url_for('tickets.view', ticket_id=ticket_id))

@tickets_bp.route('/add_comment/<int:ticket_id>', methods=['POST'])
def add_comment(ticket_id):
    """Ajouter un commentaire à un ticket"""
    try:
        comment = request.form.get('comment')
        if not comment:
            flash("Le commentaire ne peut pas être vide", "error")
            return redirect(url_for('tickets.view', ticket_id=ticket_id))
        
        # Ajouter le commentaire (nécessite une table ticket_comments)
        get_db("""
            INSERT INTO ticket_comments (ticket_id, user_id, comment, date_created)
            VALUES (?, ?, ?, ?)
        """, (ticket_id, session.get('user_id'), comment, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        flash("Commentaire ajouté avec succès", "success")
        return redirect(url_for('tickets.view', ticket_id=ticket_id))
        
    except Exception as e:
        app_logger.error(f"Erreur lors de l'ajout du commentaire: {str(e)}")
        flash("Erreur lors de l'ajout du commentaire", "error")
        return redirect(url_for('tickets.view', ticket_id=ticket_id))

@tickets_bp.route('/update/<int:ticket_id>', methods=['GET', 'POST'])
def update_ticket(ticket_id):
    """Modifier un ticket"""
    app_logger.debug(f"Méthode {request.method} reçue pour /update/{ticket_id}")
    
    # Vérifier que l'utilisateur est connecté
    if 'user_id' not in session:
        flash("Vous devez être connecté pour modifier un ticket", "error")
        return redirect(url_for('login'))
        
    if request.method == 'GET':
        try:
            app_logger.debug(f"Traitement de la requête GET pour le ticket {ticket_id}")
            # Récupérer toutes les informations nécessaires du ticket
            ticket_rows = get_db("""
                SELECT t.ID_tiqué, t.titre, t.ID_user, t.description, 
                       t.date_open, t.date_close, t.ID_technicien, 
                       t.gravite, t.open, t.tag,
                       u1.name as demandeur, u2.name as assigne_a
                FROM tiqué t
                LEFT JOIN USEUR u1 ON t.ID_user = u1.ID
                LEFT JOIN USEUR u2 ON t.ID_technicien = u2.ID
                WHERE t.ID_tiqué = ?
            """, (ticket_id,))
            if not ticket_rows:
                flash("Ticket non trouvé", "error")
                return redirect(url_for('tickets.index'))
            
            ticket = ticket_rows[0]
            users = get_db("SELECT ID, name FROM USEUR ORDER BY name")
            return render_template('tickets/update.html', ticket=ticket, ticket_id=ticket_id, users=users or [], now=datetime.now())
            
        except Exception as e:
            app_logger.error(f"Erreur lors du chargement du ticket: {str(e)}")
            flash("Erreur lors du chargement du ticket", "error")
            return redirect(url_for('tickets.index'))

    # POST - Traiter la mise à jour
    elif request.method == 'POST':
        try:
            app_logger.debug(f"Traitement de la requête POST pour la mise à jour du ticket {ticket_id}")
            # Récupérer les données du formulaire
            titre = request.form.get('titre')
            description = request.form.get('description')
            gravite = request.form.get('gravite')
            tags = request.form.get('tags')
            assigned_user_id = request.form.get('assigned_user_id')

            # Valider les données
            if not titre or not description or not gravite:
                flash("Tous les champs obligatoires doivent être remplis", "error")
                return redirect(url_for('tickets.update', ticket_id=ticket_id))

            # Mettre à jour le ticket
            get_db("""
                UPDATE tiqué 
                SET titre = ?, description = ?, gravite = ?, tag = ?,
                    ID_technicien = ?
                WHERE ID_tiqué = ?
            """, (titre, description, gravite, tags, 
                  assigned_user_id if assigned_user_id else None, ticket_id))

            flash("Ticket mis à jour avec succès", "success")
            
            # Log de l'activité
            try:
                log_activity(session.get('user_id'), 'update', 'ticket', f'Ticket {ticket_id} mis à jour')
            except:
                pass
            
            return redirect(url_for('tickets.view', ticket_id=ticket_id))
            
        except Exception as e:
            app_logger.error(f"Erreur lors de la mise à jour du ticket: {str(e)}")
            flash("Erreur lors de la mise à jour du ticket", "error")
            return redirect(url_for('tickets.view', ticket_id=ticket_id))
