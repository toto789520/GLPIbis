import sys
import os
from datetime import datetime, timedelta
import json
from ecole_directe_service import EcoleDirecteService
from db import get_db

def should_sync(last_sync, frequency):
    """
    Détermine si une synchronisation doit être effectuée en fonction de la dernière sync
    et de la fréquence configurée
    """
    if not last_sync:
        return True
        
    last_sync_date = datetime.strptime(last_sync, "%Y-%m-%d %H:%M:%S")
    now = datetime.now()
    
    if frequency == 'hourly':
        return now - last_sync_date >= timedelta(hours=1)
    elif frequency == 'daily':
        return now - last_sync_date >= timedelta(days=1)
    elif frequency == 'weekly':
        return now - last_sync_date >= timedelta(weeks=1)
    
    return False

def sync_ecoledirecte():
    """
    Effectue la synchronisation avec EcoleDirecte si nécessaire
    selon la configuration
    """
    try:
        # Récupérer la configuration
        settings = get_db("""
            SELECT setting_value 
            FROM system_settings 
            WHERE setting_key = 'ecoledirecte_credentials'
        """)
        
        if not settings:
            print("Configuration EcoleDirecte non trouvée")
            return False
        
        config = json.loads(settings[0][0])
        sync_salles = config.get('sync_salles') == '1'
        sync_edt = config.get('sync_edt') == '1'
        frequency = config.get('sync_frequency', 'daily')
        
        if not (sync_salles or sync_edt):
            print("Aucune synchronisation activée")
            return True
        
        # Créer le service avec le délai configuré
        service = EcoleDirecteService()
        
        if sync_salles and should_sync(config.get('last_sync_salles'), frequency):
            print("Synchronisation des salles...")
            print(f"Délai de temporisation configuré : {service.sync_delay} secondes")
            
            if service.synchroniser_salles():
                config['last_sync_salles'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print("Synchronisation des salles réussie")
            else:
                print("Erreur lors de la synchronisation des salles")
                return False
        
        if sync_edt and should_sync(config.get('last_sync_edt'), frequency):
            print("Synchronisation de l'emploi du temps...")
            print(f"Délai de temporisation configuré : {service.sync_delay} secondes")
            
            if service.synchroniser_emploi_du_temps():
                config['last_sync_edt'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print("Synchronisation de l'emploi du temps réussie")
            else:
                print("Erreur lors de la synchronisation de l'emploi du temps")
                return False
        
        # Mettre à jour les dates de dernière synchronisation
        get_db("""
            UPDATE system_settings 
            SET setting_value = %s 
            WHERE setting_key = 'ecoledirecte_credentials'
        """, (json.dumps(config),))
        
        return True
        
    except Exception as e:
        print(f"Erreur lors de la synchronisation: {e}")
        return False

if __name__ == '__main__':
    success = sync_ecoledirecte()
    sys.exit(0 if success else 1)