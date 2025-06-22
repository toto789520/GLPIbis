from functools import wraps
from flask import session, redirect, url_for, request, jsonify
from utils.db_manager import get_db
import logging

logger = logging.getLogger('glpibis')

def require_login(f):
    """
    Décorateur pour s'assurer qu'un utilisateur est connecté
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or 'token' not in session:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('auth.login'))
        
        # Vérifier que la session est toujours valide
        try:
            result = get_db("""
                SELECT user_id FROM sessions 
                WHERE user_id = ? AND token = ? AND datetime(expiry_date) > datetime('now')
            """, (session['user_id'], session['token']))
            
            if not result:
                session.clear()
                if request.is_json:
                    return jsonify({'error': 'Session expired'}), 401
                return redirect(url_for('auth.login'))
                
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de session: {str(e)}")
            session.clear()
            if request.is_json:
                return jsonify({'error': 'Session error'}), 500
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    return decorated_function

def require_admin(f):
    """
    Décorateur pour s'assurer qu'un utilisateur est admin
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('auth.login'))
        
        # Vérifier que l'utilisateur est admin
        try:
            result = get_db("""
                SELECT id FROM admin WHERE id_user = ?
            """, (session['user_id'],))
            
            if not result:
                if request.is_json:
                    return jsonify({'error': 'Admin access required'}), 403
                flash('Accès administrateur requis', 'error')
                return redirect(url_for('dashboard.index'))
                
        except Exception as e:
            logger.error(f"Erreur lors de la vérification admin: {str(e)}")
            if request.is_json:
                return jsonify({'error': 'Authorization error'}), 500
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    return decorated_function
