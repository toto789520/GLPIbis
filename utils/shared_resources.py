"""
Module pour partager des ressources entre différents modules de l'application
sans créer des importations circulaires.
"""
from utils.logger import app_logger

# Exporter app_logger pour qu'il puisse être importé depuis d'autres modules
# sans avoir à importer app.py directement
