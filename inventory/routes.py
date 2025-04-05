from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, Response
from utils.db import get_db, log_activity
from .inventory_service import (add_item, delete_item, get_categories, get_sous_categories, 
                              get_sous_sous_categories, list_items, get_item_by_id,
                              add_location, get_locations, update_item_location,
                              create_loan, return_item, get_active_loans, get_item_loan_history,
                              add_intervention, get_item_interventions, close_intervention,
                              export_inventory_csv, export_inventory_json, import_inventory_csv)
from datetime import datetime

# Création du Blueprint pour les routes liées à l'inventaire
inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/')
def index():
    """Page principale de l'inventaire"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    # Récupérer les catégories et le matériel
    categories = get_categories()
    print(f"DEBUG - Catégories trouvées: {len(categories) if categories else 0}")
    
    sous_categories = {}
    sous_sous_categories = {}
    hardware = []
    
    if categories:
        sous_categories = get_sous_categories(categories[0][0]) if categories else []
        print(f"DEBUG - Sous-catégories trouvées: {len(sous_categories) if sous_categories else 0}")
        
        if sous_categories:
            sous_sous_categories = get_sous_sous_categories(sous_categories[0][0])
            print(f"DEBUG - Sous-sous-catégories trouvées: {len(sous_sous_categories) if sous_sous_categories else 0}")
    
    # Liste de tous les équipements
    hardware = list_items()
    print(f"DEBUG - Matériel trouvé: {len(hardware) if hardware else 0}")
    
    # Conversion de sous_categories en dictionnaire pour le template
    sous_cat_dict = {}
    for cat in categories:
        cat_id = cat[0]
        cat_sous = get_sous_categories(cat_id)
        sous_cat_dict[cat_id] = cat_sous
    
    return render_template('inventory/index.html',
                          categories=categories,
                          sous_categories=sous_cat_dict,
                          sous_sous_categories=sous_sous_categories,
                          hardware=hardware,
                          now=datetime.now())

@inventory_bp.route('/add', methods=['GET', 'POST'])
def add():
    """Ajouter un nouvel élément à l'inventaire - redirection vers add_hardware"""
    # Rediriger vers la nouvelle version de l'interface d'ajout
    return redirect(url_for('inventory.add_hardware'))

@inventory_bp.route('/delete', methods=['POST'])
def delete():
    """Supprimer un élément de l'inventaire"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    item_id = request.form.get('id')
    if not item_id:
        flash("ID de matériel non fourni", "error")
        return redirect(url_for('inventory.index'))
    
    try:
        item = get_item_by_id(item_id)
        if not item:
            flash("Matériel introuvable", "error")
            return redirect(url_for('inventory.index'))
        
        delete_item(item_id)
        log_activity(user_id, 'delete', 'inventory', f"Matériel supprimé: {item[0]}")
        flash("Matériel supprimé avec succès!", "success")
    except Exception as e:
        flash(f"Erreur lors de la suppression: {str(e)}", "error")
    
    return redirect(url_for('inventory.index'))

@inventory_bp.route('/api/categories')
def api_categories():
    """API pour récupérer les catégories"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Non autorisé'}), 401
    
    categories = get_categories()
    return jsonify({'categories': categories})

@inventory_bp.route('/api/sous_categories/<int:categorie_id>')
def api_sous_categories(categorie_id):
    """API pour récupérer les sous-catégories d'une catégorie"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Non autorisé'}), 401
    
    sous_categories = get_sous_categories(categorie_id)
    return jsonify({'sous_categories': sous_categories})

@inventory_bp.route('/api/sous_sous_categories/<int:sous_categorie_id>')
def api_sous_sous_categories(sous_categorie_id):
    """API pour récupérer les sous-sous-catégories d'une sous-catégorie"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Non autorisé'}), 401
    
    sous_sous_categories = get_sous_sous_categories(sous_categorie_id)
    return jsonify({'sous_sous_categories': sous_sous_categories})

@inventory_bp.route('/api/items')
def api_items():
    """API pour récupérer la liste du matériel (utilisé par d'autres modules)"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Non autorisé'}), 401
    
    items = list_items()
    return jsonify({'items': items})

# Ajout des routes pour les pages créées précédemment
@inventory_bp.route('/add_hardware', methods=['GET', 'POST'])
def add_hardware():
    """Ajouter un nouveau matériel (route pour le nouveau template)"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    # Code similaire à add() mais adapté au nouveau template
    categories = get_categories()
    sous_categories = {}
    sous_sous_categories = {}
    
    # Préparer les données pour le javascript (structure de sous-catégories)
    for cat in categories:
        sous_cats = get_sous_categories(cat[0])
        sous_categories[cat[0]] = sous_cats
        
        for sous_cat in sous_cats:
            sous_sous_cats = get_sous_sous_categories(sous_cat[0])
            sous_sous_categories[sous_cat[0]] = sous_sous_cats
    
    # POST - Traitement du formulaire
    if request.method == 'POST':
        try:
            # Récupérer les données du formulaire
            nom = request.form.get('nom')
            categorie = request.form.get('categorie')
            sous_categorie = request.form.get('sous_categorie')
            sous_sous_categorie = request.form.get('sous_sous_categorie')
            date_creation = request.form.get('date_creation')
            qr_code = request.form.get('qr_code')
            description = request.form.get('description')
            
            print(f"DEBUG - Données soumises: nom={nom}, cat={categorie}, sous_cat={sous_categorie}, sous_sous_cat={sous_sous_categorie}")
            
            # Validation des données
            if not all([nom, categorie, sous_categorie, sous_sous_categorie, date_creation]):
                flash("Veuillez remplir tous les champs obligatoires", "error")
                return render_template('inventory/add_hardware.html',
                                      categories=categories,
                                      sous_categories=sous_categories,
                                      sous_sous_categories=sous_sous_categories,
                                      today=datetime.now().strftime('%Y-%m-%d'),
                                      now=datetime.now())
            
            # Ajouter le matériel à la base de données
            item_id = add_item(nom, int(categorie), int(sous_categorie), int(sous_sous_categorie), 
                              date_creation=date_creation, qr_code=qr_code)
            
            # Enregistrer l'activité
            log_activity(user_id, 'create', 'inventory', f"Matériel ajouté: {nom}")
            
            # Message de confirmation
            flash("Matériel ajouté avec succès!", "success")
            
            # Rediriger vers la page de détails du nouveau matériel
            return redirect(url_for('inventory.view_hardware', hardware_id=item_id))
            
        except Exception as e:
            flash(f"Erreur lors de l'ajout du matériel: {str(e)}", "error")
            print(f"ERREUR - Ajout matériel: {str(e)}")
    
    return render_template('inventory/add_hardware.html',
                          categories=categories,
                          sous_categories=sous_categories,
                          sous_sous_categories=sous_sous_categories,
                          today=datetime.now().strftime('%Y-%m-%d'),
                          now=datetime.now())

@inventory_bp.route('/view_hardware/<int:hardware_id>')
def view_hardware(hardware_id):
    """Afficher les détails d'un matériel"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    # TODO: Récupérer les détails du matériel
    hardware = [hardware_id, f"Matériel #{hardware_id}", "Ordinateur", "Portable", "Dell", "2023-01-01", "ABC123"]
    
    return render_template('inventory/view_hardware.html',
                          hardware=hardware,
                          description="Description de l'équipement...",
                          caracteristiques=[["Processeur", "Intel i7"], ["RAM", "16 Go"], ["SSD", "512 Go"]],
                          tickets=[],
                          historique=[],
                          now=datetime.now())

@inventory_bp.route('/generate_qr_codes')
def generate_qr_codes():
    """Générer des QR codes pour le matériel"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    # TODO: Implémenter la génération de QR codes
    flash("Fonctionnalité de génération de QR codes en développement", "info")
    return redirect(url_for('inventory.index'))

@inventory_bp.route('/edit_hardware/<int:hardware_id>', methods=['GET', 'POST'])
def edit_hardware(hardware_id):
    """Modifier un matériel existant"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    # TODO: Implémenter l'édition
    flash("Fonctionnalité d'édition en développement", "info")
    return redirect(url_for('inventory.view_hardware', hardware_id=hardware_id))

@inventory_bp.route('/delete_hardware/<int:hardware_id>', methods=['POST'])
def delete_hardware(hardware_id):
    """Supprimer un matériel"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    try:
        # Réutiliser la fonction delete_item
        delete_item(hardware_id)
        log_activity(user_id, 'delete', 'inventory', f"Matériel supprimé: ID {hardware_id}")
        flash("Matériel supprimé avec succès!", "success")
    except Exception as e:
        flash(f"Erreur lors de la suppression: {str(e)}", "error")
    
    return redirect(url_for('inventory.index'))

@inventory_bp.route('/download_qr_code/<string:qr_code>')
def download_qr_code(qr_code):
    """Télécharger le QR code d'un équipement"""
    import qrcode
    import io
    import base64
    from flask import send_file
    
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    # Créer un QR code avec les données fournies
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_code)
    qr.make(fit=True)
    
    # Générer l'image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Sauvegarder l'image dans un buffer
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    # Enregistrer cette activité
    log_activity(user_id, 'download', 'inventory', f"Téléchargement QR code: {qr_code}")
    
    # Envoyer le fichier au client
    return send_file(img_buffer, mimetype='image/png', as_attachment=True, 
                     download_name=f'qr_code_{qr_code}.png')

# Routes pour la localisation
@inventory_bp.route('/locations', methods=['GET', 'POST'])
def locations():
    """Gérer les localisations"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        batiment = request.form.get('batiment')
        etage = request.form.get('etage')
        salle = request.form.get('salle')
        description = request.form.get('description')
        
        try:
            location_id = add_location(batiment, etage, salle, description)
            flash("Localisation ajoutée avec succès!", "success")
        except Exception as e:
            flash(f"Erreur lors de l'ajout de la localisation: {str(e)}", "error")
    
    locations = get_locations()
    return render_template('inventory/locations.html', locations=locations)

@inventory_bp.route('/item/<int:item_id>/location', methods=['POST'])
def update_location(item_id):
    """Mettre à jour la localisation d'un matériel"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    location_id = request.form.get('location_id')
    try:
        update_item_location(item_id, location_id)
        flash("Localisation mise à jour avec succès!", "success")
    except Exception as e:
        flash(f"Erreur lors de la mise à jour de la localisation: {str(e)}", "error")
    
    return redirect(url_for('inventory.view_hardware', hardware_id=item_id))

# Routes pour les prêts
@inventory_bp.route('/loans')
def loans():
    """Liste des prêts en cours"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    active_loans = get_active_loans()
    return render_template('inventory/loans.html', loans=active_loans)

@inventory_bp.route('/item/<int:item_id>/loan', methods=['GET', 'POST'])
def loan_item(item_id):
    """Emprunter un matériel"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        return_date = request.form.get('return_date')
        notes = request.form.get('notes')
        
        try:
            create_loan(item_id, user_id, return_date, notes)
            flash("Prêt enregistré avec succès!", "success")
        except Exception as e:
            flash(f"Erreur lors de l'enregistrement du prêt: {str(e)}", "error")
    
    return redirect(url_for('inventory.view_hardware', hardware_id=item_id))

@inventory_bp.route('/loan/<int:loan_id>/return', methods=['POST'])
def return_loan(loan_id):
    """Retourner un matériel emprunté"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    try:
        return_item(loan_id)
        flash("Retour enregistré avec succès!", "success")
    except Exception as e:
        flash(f"Erreur lors de l'enregistrement du retour: {str(e)}", "error")
    
    return redirect(url_for('inventory.loans'))

# Routes pour les interventions
@inventory_bp.route('/item/<int:item_id>/intervention', methods=['POST'])
def add_item_intervention(item_id):
    """Ajouter une intervention sur un matériel"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    type_intervention = request.form.get('type')
    description = request.form.get('description')
    
    try:
        add_intervention(item_id, user_id, type_intervention, description)
        flash("Intervention enregistrée avec succès!", "success")
    except Exception as e:
        flash(f"Erreur lors de l'enregistrement de l'intervention: {str(e)}", "error")
    
    return redirect(url_for('inventory.view_hardware', hardware_id=item_id))

@inventory_bp.route('/intervention/<int:intervention_id>/close', methods=['POST'])
def close_item_intervention(intervention_id):
    """Terminer une intervention"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    try:
        close_intervention(intervention_id)
        flash("Intervention terminée avec succès!", "success")
    except Exception as e:
        flash(f"Erreur lors de la clôture de l'intervention: {str(e)}", "error")
    
    return redirect(request.referrer or url_for('inventory.index'))

# Routes pour l'import/export
@inventory_bp.route('/export/<format>')
def export_inventory(format):
    """Exporter l'inventaire (CSV ou JSON)"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    try:
        if format == 'csv':
            output = export_inventory_csv()
            mimetype = 'text/csv'
            filename = 'inventaire.csv'
        elif format == 'json':
            output = export_inventory_json()
            mimetype = 'application/json'
            filename = 'inventaire.json'
        else:
            flash("Format d'export non supporté", "error")
            return redirect(url_for('inventory.index'))
        
        # Log de l'activité
        log_activity(user_id, 'export', 'inventory', f"Export {format.upper()} de l'inventaire")
        
        # Envoyer le fichier
        return Response(
            output,
            mimetype=mimetype,
            headers={'Content-Disposition': f'attachment;filename={filename}'}
        )
        
    except Exception as e:
        flash(f"Erreur lors de l'export: {str(e)}", "error")
        return redirect(url_for('inventory.index'))

@inventory_bp.route('/import', methods=['POST'])
def import_inventory():
    """Importer l'inventaire depuis un fichier CSV"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    if 'file' not in request.files:
        flash("Aucun fichier sélectionné", "error")
        return redirect(url_for('inventory.index'))
    
    file = request.files['file']
    if file.filename == '':
        flash("Aucun fichier sélectionné", "error")
        return redirect(url_for('inventory.index'))
    
    if not file.filename.endswith('.csv'):
        flash("Format de fichier non supporté. Utilisez un fichier CSV.", "error")
        return redirect(url_for('inventory.index'))
    
    try:
        file_content = file.read().decode('utf-8')
        imported_count, errors = import_inventory_csv(file_content)
        
        # Log de l'activité
        log_activity(user_id, 'import', 'inventory', f"Import CSV: {imported_count} éléments importés")
        
        if errors:
            flash(f"Import terminé avec {len(errors)} erreurs. {imported_count} éléments importés.", "warning")
            for error in errors:
                flash(error, "error")
        else:
            flash(f"Import terminé avec succès. {imported_count} éléments importés.", "success")
            
    except Exception as e:
        flash(f"Erreur lors de l'import: {str(e)}", "error")
    
    return redirect(url_for('inventory.index'))