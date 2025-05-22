"""
Service de gestion des commentaires pour les tickets
"""
import datetime
import logging
from utils.db_manager import get_db, log_activity

logger = logging.getLogger('glpibis')

class CommentService:
    @staticmethod
    def add_comment(ticket_id, user_id, content, gravite=0):
        """
        Ajoute un commentaire à un ticket
        
        Args:
            ticket_id (int): ID du ticket
            user_id (str): ID de l'utilisateur
            content (str): Contenu du commentaire
            gravite (int, optional): Niveau de gravité. Defaults to 0.
            
        Returns:
            bool: True si le commentaire a été ajouté avec succès
            
        Raises:
            ValueError: Si le ticket n'existe pas ou si le contenu est vide
        """
        try:
            # Validation des entrées
            if not content or not content.strip():
                raise ValueError("Le contenu du commentaire ne peut pas être vide")
                
            # Vérifier que le ticket existe
            ticket = get_db("SELECT ID_tiqué, open FROM tiqué WHERE ID_tiqué = ?", (ticket_id,))
            if not ticket:
                raise ValueError(f"Le ticket {ticket_id} n'existe pas")
                
            # S'assurer que gravite est dans la plage 0-5
            try:
                gravite = max(0, min(5, int(gravite)))
            except (ValueError, TypeError):
                gravite = 0
                
            # Insérer le commentaire
            get_db("""INSERT INTO ticket_comments 
                     (ticket_id, user_id, content, gravite, created_at) 
                     VALUES (?, ?, ?, ?, ?)""", 
                   (ticket_id, user_id, content, gravite, datetime.datetime.now()))
                   
            # Enregistrer l'activité
            log_activity(user_id, 'comment', 'ticket', f"Commentaire ajouté au ticket {ticket_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout du commentaire: {str(e)}")
            raise

    @staticmethod
    def get_comments(ticket_id, with_user_info=True):
        """
        Récupère tous les commentaires d'un ticket
        
        Args:
            ticket_id (int): ID du ticket
            with_user_info (bool): Inclure les informations sur l'utilisateur
            
        Returns:
            list: Liste des commentaires avec leurs détails
        """
        try:
            if with_user_info:
                comments = get_db("""
                    SELECT c.*, u.name as user_name
                    FROM ticket_comments c
                    LEFT JOIN USEUR u ON c.user_id = u.ID
                    WHERE c.ticket_id = ?
                    ORDER BY c.created_at DESC
                """, (ticket_id,))
            else:
                comments = get_db("""
                    SELECT *
                    FROM ticket_comments
                    WHERE ticket_id = ?
                    ORDER BY created_at DESC
                """, (ticket_id,))
            
            return comments
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des commentaires: {str(e)}")
            return []

    @staticmethod
    def delete_comment(comment_id, user_id):
        """
        Supprime un commentaire
        
        Args:
            comment_id (int): ID du commentaire
            user_id (str): ID de l'utilisateur essayant de supprimer
            
        Returns:
            bool: True si le commentaire a été supprimé
            
        Raises:
            ValueError: Si le commentaire n'existe pas ou si l'utilisateur n'a pas les droits
        """
        try:
            # Vérifier que le commentaire existe et appartient à l'utilisateur
            comment = get_db("""
                SELECT ticket_id 
                FROM ticket_comments 
                WHERE id = ? AND user_id = ?
            """, (comment_id, user_id))
            
            if not comment:
                raise ValueError("Le commentaire n'existe pas ou vous n'avez pas les droits pour le supprimer")
                
            # Supprimer le commentaire
            get_db("DELETE FROM ticket_comments WHERE id = ?", (comment_id,))
            
            # Enregistrer l'activité
            log_activity(user_id, 'delete_comment', 'ticket', f"Commentaire {comment_id} supprimé")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du commentaire: {str(e)}")
            raise

    @staticmethod 
    def update_comment(comment_id, user_id, new_content, new_gravite=None):
        """
        Modifie un commentaire existant
        
        Args:
            comment_id (int): ID du commentaire
            user_id (str): ID de l'utilisateur
            new_content (str): Nouveau contenu du commentaire
            new_gravite (int, optional): Nouvelle gravité
            
        Returns:
            bool: True si le commentaire a été modifié
            
        Raises:
            ValueError: Si le commentaire n'existe pas ou si l'utilisateur n'a pas les droits
        """
        try:
            if not new_content or not new_content.strip():
                raise ValueError("Le contenu du commentaire ne peut pas être vide")
                
            # Vérifier que le commentaire existe et appartient à l'utilisateur
            comment = get_db("""
                SELECT id
                FROM ticket_comments 
                WHERE id = ? AND user_id = ?
            """, (comment_id, user_id))
            
            if not comment:
                raise ValueError("Le commentaire n'existe pas ou vous n'avez pas les droits pour le modifier")
                
            # Mettre à jour le commentaire
            if new_gravite is not None:
                gravite = max(0, min(5, int(new_gravite)))
                get_db("""
                    UPDATE ticket_comments 
                    SET content = ?, gravite = ?
                    WHERE id = ?
                """, (new_content, gravite, comment_id))
            else:
                get_db("""
                    UPDATE ticket_comments 
                    SET content = ?
                    WHERE id = ?
                """, (new_content, comment_id))
                
            # Enregistrer l'activité
            log_activity(user_id, 'update_comment', 'ticket', f"Commentaire {comment_id} modifié")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la modification du commentaire: {str(e)}")
            raise
