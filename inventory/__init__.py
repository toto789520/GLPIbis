"""
Module Inventory pour GLPIbis
Gestion de l'inventaire du matériel informatique
"""

__version__ = '1.0.0'
__author__ = 'GLPIbis Team'

from .routes import inventory_bp

__all__ = ['inventory_bp']

# Ce fichier rend le dossier inventory un module Python