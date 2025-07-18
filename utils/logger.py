import os
import logging
from logging.handlers import RotatingFileHandler
import datetime

_logger_instance = None

def setup_logger():
    """Configure et retourne le logger principal de l'application"""
    global _logger_instance
    
    if _logger_instance:
        return _logger_instance
    
    # Créer le logger
    logger = logging.getLogger('glpibis')
    logger.setLevel(logging.DEBUG)
    
    # Éviter la duplication des handlers
    if logger.handlers:
        return logger
    
    # Créer le dossier logs s'il n'existe pas
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Configuration du fichier de log
    log_file = os.path.join(log_dir, f'glpibis--{datetime.datetime.now().strftime("%Y-%m-%d")}.log')
    
    # Format de log
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    try:
        # Handler fichier
        file_handler = RotatingFileHandler(log_file, maxBytes=1024*1024, backupCount=5)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
        
        # Handler console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.DEBUG)
        logger.addHandler(console_handler)
        
        logger.info(f"Logger configuré avec succès - fichier: {log_file}")
    except Exception as e:
        # Logger de secours console uniquement
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        logger.error(f"Erreur configuration logger: {str(e)}")
    
    _logger_instance = logger
    return logger

# Instance globale du logger
app_logger = setup_logger()

def get_logger(name=None):
    """Retourne une instance du logger"""
    if name:
        return logging.getLogger(name)
    return app_logger
