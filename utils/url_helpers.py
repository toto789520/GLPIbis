from flask import url_for
import logging

app_logger = logging.getLogger("glpibis")

def safe_url_for(endpoint, **values):
    """
    Version sécurisée de url_for qui gère les erreurs gracieusement
    """
    try:
        return url_for(endpoint, **values)
    except Exception as e:
        app_logger.warning(f"Endpoint non trouvé: {endpoint} -> {endpoint}")
        # Fallback vers l'index si l'endpoint n'existe pas
        try:
            return url_for('index')
        except:
            return '/'
