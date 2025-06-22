from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app
from utils.db_manager import get_db
from utils.logger import get_logger
from datetime import datetime
import traceback
from inventory.qr_service import QRCodeService
import os

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')
app_logger = get_logger()

@inventory_bp.route('/')
def index():
    """Page d'accueil de l'inventaire"""
    try:
        app_logger.debug("DEBUG - inventory.index: Affichage de la page d'inventaire")
        
        # Récupérer les statistiques de l'inventaire
        stats = {
            'total_elements': 0,
            'elements_actifs': 0,
            'en_maintenance': 0,
            'garantie_expiree': 0
        }
        
        try:
            # Vérifier si la table inventory existe, sinon la créer
            get_db("""
                CREATE TABLE IF NOT EXISTS inventory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    location TEXT,
                    status TEXT DEFAULT 'active',
                    serial_number TEXT,
                    purchase_date DATE,
                    warranty_end DATE,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Récupérer les statistiques
            total_result = get_db("SELECT COUNT(*) FROM inventory")
            stats['total_elements'] = total_result[0][0] if total_result else 0
            
            active_result = get_db("SELECT COUNT(*) FROM inventory WHERE status = 'active'")
            stats['elements_actifs'] = active_result[0][0] if active_result else 0
            
            maintenance_result = get_db("SELECT COUNT(*) FROM inventory WHERE status = 'maintenance'")
            stats['en_maintenance'] = maintenance_result[0][0] if maintenance_result else 0
            
            expired_result = get_db("SELECT COUNT(*) FROM inventory WHERE warranty_end < date('now') AND warranty_end IS NOT NULL")
            stats['garantie_expiree'] = expired_result[0][0] if expired_result else 0
            
        except Exception as db_error:
            app_logger.error(f"Erreur lors de la récupération des statistiques: {str(db_error)}")
        
        # Récupérer les éléments d'inventaire avec recherche et filtres
        search = request.args.get('search', '')
        category_filter = request.args.get('category', '')
        status_filter = request.args.get('status', '')
        
        query = "SELECT * FROM inventory WHERE 1=1"
        params = []
        
        if search:
            query += " AND (name LIKE ? OR description LIKE ? OR serial_number LIKE ?)"
            search_param = f"%{search}%"
            params.extend([search_param, search_param, search_param])
        
        if category_filter:
            query += " AND category = ?"
            params.append(category_filter)
        
        if status_filter:
            query += " AND status = ?"
            params.append(status_filter)
        
        query += " ORDER BY created_at DESC"
        
        inventory_items = get_db(query, params) or []
        
        # Traiter les dates pour éviter les erreurs de comparaison
        processed_items = []
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        for item in inventory_items:
            # Convertir l'item en liste pour pouvoir le modifier
            item_list = list(item)
            
            # Vérifier et traiter la date de garantie (index 7)
            if item_list[7]:
                try:
                    # S'assurer que la date est dans le bon format
                    warranty_date = item_list[7]
                    if isinstance(warranty_date, str):
                        # Valider le format de date
                        datetime.strptime(warranty_date, '%Y-%m-%d')
                except (ValueError, TypeError):
                    # Si la date n'est pas valide, la mettre à None
                    item_list[7] = None
                    app_logger.warning(f"Date de garantie invalide pour l'item {item_list[0]}: {warranty_date}")
            
            processed_items.append(item_list)
        
        # Récupérer les catégories disponibles pour les filtres
        categories = get_db("SELECT DISTINCT category FROM inventory ORDER BY category") or []
        category_list = [cat[0] for cat in categories]
        
        return render_template('inventory/index.html', 
                             inventory_items=processed_items,
                             stats=stats,
                             categories=category_list,
                             search=search,
                             category_filter=category_filter,
                             status_filter=status_filter,
                             current_date=current_date)
                             
    except Exception as e:
        app_logger.error(f"Erreur dans inventory.index: {str(e)}")
        app_logger.error(traceback.format_exc())
        flash(f"Erreur lors du chargement de l'inventaire: {str(e)}", "error")
        return render_template('inventory/index.html', 
                             inventory_items=[],
                             stats={'total_elements': 0, 'elements_actifs': 0, 'en_maintenance': 0, 'garantie_expiree': 0},
                             categories=[],
                             current_date=datetime.now().strftime('%Y-%m-%d'))

@inventory_bp.route('/create', methods=['GET', 'POST'])
def create_item():
    """Créer un nouvel élément d'inventaire"""
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            category = request.form.get('category')
            location = request.form.get('location')
            status = request.form.get('status', 'active')
            serial_number = request.form.get('serial_number')
            purchase_date = request.form.get('purchase_date')
            warranty_end = request.form.get('warranty_end')
            description = request.form.get('description')
            
            if not name or not category:
                flash("Le nom et la catégorie sont obligatoires", "error")
                return render_template('inventory/create.html')
            
            # Insérer le nouvel élément
            get_db("""
                INSERT INTO inventory (name, category, location, status, serial_number, 
                                     purchase_date, warranty_end, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, category, location, status, serial_number, 
                  purchase_date if purchase_date else None,
                  warranty_end if warranty_end else None,
                  description))
            
            app_logger.info(f"Nouvel élément d'inventaire créé: {name}")
            flash(f"Élément '{name}' ajouté avec succès à l'inventaire", "success")
            return redirect(url_for('inventory.index'))
            
        except Exception as e:
            app_logger.error(f"Erreur lors de la création de l'élément: {str(e)}")
            flash(f"Erreur lors de la création: {str(e)}", "error")
    
    return render_template('inventory/create.html')

@inventory_bp.route('/item/<int:item_id>')
def view_item(item_id):
    """Voir les détails d'un élément d'inventaire"""
    try:
        item = get_db("SELECT * FROM inventory WHERE id = ?", (item_id,))
        if not item:
            flash("Élément non trouvé", "error")
            return redirect(url_for('inventory.index'))
        
        return render_template('inventory/view.html', item=item[0])
        
    except Exception as e:
        app_logger.error(f"Erreur lors de la visualisation de l'élément {item_id}: {str(e)}")
        flash(f"Erreur lors du chargement: {str(e)}", "error")
        return redirect(url_for('inventory.index'))

@inventory_bp.route('/item/<int:item_id>/edit', methods=['GET', 'POST'])
def edit_item(item_id):
    """Modifier un élément d'inventaire"""
    try:
        item = get_db("SELECT * FROM inventory WHERE id = ?", (item_id,))
        if not item:
            flash("Élément non trouvé", "error")
            return redirect(url_for('inventory.index'))
        
        if request.method == 'POST':
            name = request.form.get('name')
            category = request.form.get('category')
            location = request.form.get('location')
            status = request.form.get('status')
            serial_number = request.form.get('serial_number')
            purchase_date = request.form.get('purchase_date')
            warranty_end = request.form.get('warranty_end')
            description = request.form.get('description')
            
            if not name or not category:
                flash("Le nom et la catégorie sont obligatoires", "error")
                return render_template('inventory/edit.html', item=item[0])
            
            # Mettre à jour l'élément
            get_db("""
                UPDATE inventory 
                SET name = ?, category = ?, location = ?, status = ?, 
                    serial_number = ?, purchase_date = ?, warranty_end = ?, description = ?
                WHERE id = ?
            """, (name, category, location, status, serial_number,
                  purchase_date if purchase_date else None,
                  warranty_end if warranty_end else None,
                  description, item_id))
            
            app_logger.info(f"Élément d'inventaire {item_id} modifié: {name}")
            flash(f"Élément '{name}' modifié avec succès", "success")
            return redirect(url_for('inventory.view_item', item_id=item_id))
        
        return render_template('inventory/edit.html', item=item[0])
        
    except Exception as e:
        app_logger.error(f"Erreur lors de la modification de l'élément {item_id}: {str(e)}")
        flash(f"Erreur lors de la modification: {str(e)}", "error")
        return redirect(url_for('inventory.index'))

@inventory_bp.route('/generate-qr/<int:item_id>', methods=['POST'])
def generate_qr_code(item_id):
    """Génère un QR code pour un équipement"""
    try:
        # Récupérer les informations de l'équipement depuis inventory
        item = get_db("SELECT * FROM inventory WHERE id = ?", (item_id,))
        
        if not item:
            return jsonify({'success': False, 'error': 'Équipement non trouvé'}), 404
        
        # Initialiser le service QR
        static_folder = current_app.static_folder
        qr_service = QRCodeService(static_folder)
        
        # Préparer les informations de l'équipement
        equipment_info = {
            'id': item[0][0],
            'name': item[0][1],
            'category': item[0][2],
            'location': item[0][3],
            'status': item[0][4],
            'serial': item[0][5],
            'purchase_date': item[0][6],
            'warranty_end': item[0][7],
            'created_at': item[0][9]
        }
        
        # Générer le QR code simple
        filename = qr_service.generate_qr_code(equipment_info['id'], equipment_info['name'])
        
        # Générer aussi l'étiquette complète
        label_filename = qr_service.generate_qr_label(equipment_info)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'label_filename': label_filename,
            'message': f'QR code généré pour {equipment_info["name"]}'
        })
        
    except Exception as e:
        app_logger.error(f"Erreur lors de la génération du QR code: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@inventory_bp.route('/scan-qr', methods=['GET', 'POST'])
def scan_qr():
    """Page de scan de QR codes"""
    if request.method == 'POST':
        if 'qr_image' not in request.files:
            return jsonify({'success': False, 'error': 'Aucun fichier fourni'}), 400
        
        file = request.files['qr_image']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Aucun fichier sélectionné'}), 400
        
        try:
            # Lire le QR code
            static_folder = current_app.static_folder
            qr_service = QRCodeService(static_folder)
            
            hardware_id = qr_service.get_qr_info(file.read())
            
            if hardware_id:
                return jsonify({
                    'success': True,
                    'hardware_id': hardware_id,
                    'redirect_url': f'/inventory/item/{hardware_id}'
                })
            else:
                return jsonify({'success': False, 'error': 'QR code non reconnu'}), 400
                
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    return render_template('inventory/scan_qr.html')
