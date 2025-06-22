import os
import logging
from logging.handlers import RotatingFileHandler
import datetime

_logger_instance = None

def get_logger(name=None):
    """
    Configure et retourne un logger pour l'application
    """
    global _logger_instance
    
    if name is None:
        name = 'glpibis'
    
    logger = logging.getLogger(name)
    
    # Éviter la duplication des handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # Créer le dossier logs s'il n'existe pas
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Fichier de log
    log_file = os.path.join(log_dir, f'glpibis--{datetime.datetime.now().strftime("%Y-%m-%d")}.log')

    log_formatter = logging.Formatter('%(process)d - %(asctime)s - %(name)s - %(levelname)s - %(message)s')

    try:
        handler = RotatingFileHandler(log_file, maxBytes=1024*1024, backupCount=5)
        handler.setFormatter(log_formatter)
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_formatter)
        console_handler.setLevel(logging.DEBUG)
        logger.addHandler(console_handler)

        logger.info(f"Logger configuré avec fichier : {log_file}")
    except Exception as e:
        # Fallback logger with console only
        logger = logging.getLogger('glpibis')
        logger.setLevel(logging.DEBUG)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_formatter)
        logger.addHandler(console_handler)
        logger.error(f"ERREUR CRITIQUE - Impossible de configurer le logger : {str(e)}")
    
    _logger_instance = logger
    return _logger_instance

def setup_logger():
    """Fonction pour initialiser le logger au démarrage de l'application"""
    return get_logger()
    """Fonction pour initialiser le logger au démarrage de l'application"""
    return get_logger()
