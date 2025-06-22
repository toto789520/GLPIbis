import datetime
import secrets
import csv
import json
from io import StringIO
from utils.db_manager import get_db
from utils.logger import app_logger
import traceback
from datetime import datetime

class InventoryService:
    def __init__(self):
        """Initialise le service d'inventaire"""
        self.ensure_inventory_table()
    
    def ensure_inventory_table(self):
        """S'assure que la table inventory existe avec la bonne structure"""
        try:
            # Créer la table inventory si elle n'existe pas
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            app_logger.info("Table inventory vérifiée/créée avec succès")
        except Exception as e:
            app_logger.error(f"Erreur lors de la création de la table inventory: {str(e)}")
            raise
    
    def get_all_items(self, search_term=None, category_filter=None, status_filter=None):
        """Récupère tous les éléments d'inventaire avec filtres optionnels"""
        try:
            base_query = """
                SELECT id, name, category, location, status, serial_number, 
                       purchase_date, warranty_end, description, created_at
                FROM inventory 
                WHERE 1=1
            """
            params = []
            
            # Ajouter les filtres de recherche de manière sécurisée
            if search_term:
                base_query += " AND (name LIKE ? OR description LIKE ? OR serial_number LIKE ?)"
                search_pattern = f"%{search_term}%"
                params.extend([search_pattern, search_pattern, search_pattern])
            
            if category_filter and category_filter != 'all':
                base_query += " AND category = ?"
                params.append(category_filter)
            
            if status_filter and status_filter != 'all':
                base_query += " AND status = ?"
                params.append(status_filter)
            
            base_query += " ORDER BY created_at DESC"
            
            # Exécuter la requête
            result = get_db(base_query, params)
            
            # Convertir les résultats en liste de dictionnaires pour une manipulation plus facile
            items = []
            if result:
                for row in result:
                    # S'assurer que row est bien un tuple/liste avec au moins 10 éléments
                    if isinstance(row, (tuple, list)) and len(row) >= 10:
                        item = {
                            'id': row[0],
                            'name': row[1],
                            'category': row[2],
                            'location': row[3],
                            'status': row[4],
                            'serial_number': row[5],
                            'purchase_date': row[6],
                            'warranty_end': row[7],
                            'description': row[8],
                            'created_at': row[9]
                        }
                        items.append(item)
                    else:
                        app_logger.warning(f"Format de données inattendu pour l'élément d'inventaire: {row}")
            
            app_logger.debug(f"Récupération de {len(items)} éléments d'inventaire")
            return items
            
        except Exception as e:
            app_logger.error(f"Erreur lors de la récupération des éléments d'inventaire: {str(e)}")
            app_logger.error(traceback.format_exc())
            return []
    
    def get_item_by_id(self, item_id):
        """Récupère un élément d'inventaire par son ID"""
        try:
            result = get_db("""
                SELECT id, name, category, location, status, serial_number, 
                       purchase_date, warranty_end, description, created_at, updated_at
                FROM inventory 
                WHERE id = ?
            """, (item_id,))
            
            if result and len(result) > 0:
                row = result[0]
                if isinstance(row, (tuple, list)) and len(row) >= 11:
                    return {
                        'id': row[0],
                        'name': row[1],
                        'category': row[2],
                        'location': row[3],
                        'status': row[4],
                        'serial_number': row[5],
                        'purchase_date': row[6],
                        'warranty_end': row[7],
                        'description': row[8],
                        'created_at': row[9],
                        'updated_at': row[10]
                    }
            
            return None
            
        except Exception as e:
            app_logger.error(f"Erreur lors de la récupération de l'élément {item_id}: {str(e)}")
            return None
    
    def create_item(self, data):
        """Crée un nouvel élément d'inventaire"""
        try:
            result = get_db("""
                INSERT INTO inventory (name, category, location, status, serial_number, 
                                     purchase_date, warranty_end, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('name'),
                data.get('category'),
                data.get('location'),
                data.get('status', 'active'),
                data.get('serial_number'),
                data.get('purchase_date'),
                data.get('warranty_end'),
                data.get('description')
            ))
            
            # Récupérer l'ID du nouvel élément
            last_id = get_db("SELECT last_insert_rowid()")[0][0]
            app_logger.info(f"Nouvel élément d'inventaire créé avec l'ID: {last_id}")
            return last_id
            
        except Exception as e:
            app_logger.error(f"Erreur lors de la création de l'élément: {str(e)}")
            raise
    
    def update_item(self, item_id, data):
        """Met à jour un élément d'inventaire"""
        try:
            get_db("""
                UPDATE inventory 
                SET name = ?, category = ?, location = ?, status = ?, 
                    serial_number = ?, purchase_date = ?, warranty_end = ?, 
                    description = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                data.get('name'),
                data.get('category'),
                data.get('location'),
                data.get('status'),
                data.get('serial_number'),
                data.get('purchase_date'),
                data.get('warranty_end'),
                data.get('description'),
                item_id
            ))
            
            app_logger.info(f"Élément d'inventaire {item_id} mis à jour")
            return True
            
        except Exception as e:
            app_logger.error(f"Erreur lors de la mise à jour de l'élément {item_id}: {str(e)}")
            return False
    
    def delete_item(self, item_id):
        """Supprime un élément d'inventaire"""
        try:
            get_db("DELETE FROM inventory WHERE id = ?", (item_id,))
            app_logger.info(f"Élément d'inventaire {item_id} supprimé")
            return True
            
        except Exception as e:
            app_logger.error(f"Erreur lors de la suppression de l'élément {item_id}: {str(e)}")
            return False
    
    def get_categories(self):
        """Récupère toutes les catégories d'inventaire disponibles"""
        try:
            result = get_db("SELECT DISTINCT category FROM inventory ORDER BY category")
            categories = [row[0] for row in result if row and len(row) > 0]
            return categories
        except Exception as e:
            app_logger.error(f"Erreur lors de la récupération des catégories: {str(e)}")
            return []
    
    def get_statistics(self):
        """Récupère les statistiques de l'inventaire"""
        try:
            stats = {}
            
            # Total des éléments
            total_result = get_db("SELECT COUNT(*) FROM inventory")
            stats['total'] = total_result[0][0] if total_result and total_result[0] else 0
            
            # Éléments actifs
            active_result = get_db("SELECT COUNT(*) FROM inventory WHERE status = 'active'")
            stats['active'] = active_result[0][0] if active_result and active_result[0] else 0
            
            # Éléments en maintenance
            maintenance_result = get_db("SELECT COUNT(*) FROM inventory WHERE status = 'maintenance'")
            stats['maintenance'] = maintenance_result[0][0] if maintenance_result and maintenance_result[0] else 0
            
            # Éléments avec garantie expirée
            expired_result = get_db("""
                SELECT COUNT(*) FROM inventory 
                WHERE warranty_end IS NOT NULL AND warranty_end < date('now')
            """)
            stats['expired_warranty'] = expired_result[0][0] if expired_result and expired_result[0] else 0
            
            return stats
            
        except Exception as e:
            app_logger.error(f"Erreur lors du calcul des statistiques: {str(e)}")
            return {'total': 0, 'active': 0, 'maintenance': 0, 'expired_warranty': 0}

# Instance globale du service
inventory_service = InventoryService()