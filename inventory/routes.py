from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from utils.db import get_db, log_activity
from .inventory_service import add_item, delete_item, get_categories, get_sous_categories, get_sous_sous_categories, list_items, get_item_by_id
from datetime import datetime

# Création du Blueprint pour les routes liées à l'inventaire
inventory_bp = Blueprint('inventory', __name__, template_folder='templates')

@inventory_bp.route('/')
def index():
    """Page principale de l'inventaire"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    # Récupérer les catégories et le matériel
    categories = get_categories()
    sous_categories = get_sous_categories(categories[0][0]) if categories else []
    sous_sous_categories = get_sous_sous_categories(sous_categories[0][0]) if sous_categories else []
    
    # Liste de tous les équipements
    items = list_items()
    
    return render_template('inventory/index.html',
                          categories=categories,
                          sous_categories=sous_categories,
                          sous_sous_categories=sous_sous_categories,
                          items=items,
                          now=datetime.now())

@inventory_bp.route('/add', methods=['GET', 'POST'])
def add():
    """Ajouter un nouvel élément à l'inventaire"""
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        nom = request.form.get('nom')
        categorie = request.form.get('categorie')
        sous_categorie = request.form.get('sous_categorie')
        sous_sous_categorie = request.form.get('sous_sous_categorie')
        
        if not all([nom, categorie, sous_categorie, sous_sous_categorie]):
            flash("Veuillez remplir tous les champs", "error")
            return redirect(url_for('inventory.add'))
        
        try:
            item_id = add_item(nom, int(categorie), int(sous_categorie), int(sous_sous_categorie))
            log_activity(user_id, 'create', 'inventory', f"Matériel ajouté: {nom}")
            flash("Matériel ajouté avec succès!", "success")
            return redirect(url_for('inventory.index'))
        except Exception as e:
            flash(f"Erreur lors de l'ajout du matériel: {str(e)}", "error")
            
    # GET request - afficher le formulaire
    categories = get_categories()
    sous_categories = get_sous_categories(categories[0][0]) if categories else []
    sous_sous_categories = get_sous_sous_categories(sous_categories[0][0]) if sous_categories else []
    
    return render_template('inventory/add.html',
                          categories=categories,
                          sous_categories=sous_categories,
                          sous_sous_categories=sous_sous_categories,
                          now=datetime.now())

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
        # TODO: Implémenter le traitement du formulaire
        pass
    
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