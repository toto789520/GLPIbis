import requests
from datetime import datetime, timedelta
import json
import time
from utils.db import get_db, log_activity

class EcoleDirecteService:
    BASE_URL = "https://api.ecoledirecte.com/v3"
    
    def __init__(self):
        self.token = None
        self._load_credentials()
    
    def _load_credentials(self):
        """Charge les identifiants depuis la configuration"""
        try:
            settings = get_db("SELECT setting_value FROM system_settings WHERE setting_key = 'ecoledirecte_credentials'")
            if settings:
                credentials = json.loads(settings[0][0])
                self.username = credentials.get('username')
                self.password = credentials.get('password')
                self.sync_delay = int(credentials.get('sync_delay', '30'))
            else:
                raise ValueError("Identifiants EcoleDirecte non configurés")
        except Exception as e:
            print(f"Erreur lors du chargement des identifiants: {e}")
            raise
    
    def _api_call(self, method, endpoint, data=None, params=None):
        """
        Effectue un appel API avec gestion du délai de temporisation
        """
        try:
            if self.sync_delay > 0:
                time.sleep(self.sync_delay)  # Attendre le délai configuré
                
            response = requests.request(
                method,
                f"{self.BASE_URL}/{endpoint}",
                json=data,
                params=params,
                headers={"X-Token": self.token} if self.token else None
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Erreur lors de l'appel API {endpoint}: {e}")
            return None
    
    def login(self):
        """Se connecte à l'API EcoleDirecte"""
        try:
            data = self._api_call(
                "POST", 
                "login",
                data={"username": self.username, "password": self.password}
            )
            
            if data and data.get('token'):
                self.token = data['token']
                return True
            return False
        except Exception as e:
            print(f"Erreur de connexion à EcoleDirecte: {e}")
            return False
    
    def get_emploi_du_temps(self, date_debut=None, date_fin=None):
        """
        Récupère l'emploi du temps pour une période donnée
        
        Args:
            date_debut (str): Date de début au format YYYY-MM-DD
            date_fin (str): Date de fin au format YYYY-MM-DD
        """
        if not self.token and not self.login():
            raise Exception("Non authentifié à EcoleDirecte")
        
        if not date_debut:
            date_debut = datetime.now().strftime("%Y-%m-%d")
        if not date_fin:
            date_fin = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        return self._api_call(
            "GET",
            f"E/{self.username}/emploidutemps",
            params={"dateDebut": date_debut, "dateFin": date_fin}
        )
    
    def get_salles(self):
        """Récupère la liste des salles"""
        if not self.token and not self.login():
            raise Exception("Non authentifié à EcoleDirecte")
        
        return self._api_call(
            "GET",
            f"E/{self.username}/salles"
        )
    
    def synchroniser_salles(self):
        """
        Synchronise les salles d'EcoleDirecte avec la base de données locale
        """
        try:
            salles = self.get_salles()
            if not salles:
                return False
            
            # Créer une table de correspondance si elle n'existe pas
            get_db("""
                CREATE TABLE IF NOT EXISTS ecoledirecte_salles (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    id_ecoledirecte VARCHAR(50) NOT NULL UNIQUE,
                    nom VARCHAR(255) NOT NULL,
                    batiment VARCHAR(100),
                    etage VARCHAR(50),
                    capacite INT,
                    last_sync DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_id_ecoledirecte (id_ecoledirecte)
                )
            """)
            
            # Mettre à jour ou insérer les salles
            for salle in salles['data']:
                existing = get_db(
                    "SELECT id FROM ecoledirecte_salles WHERE id_ecoledirecte = %s",
                    (salle['id'],)
                )
                
                if existing:
                    # Mettre à jour la salle existante
                    get_db("""
                        UPDATE ecoledirecte_salles 
                        SET nom = %s, batiment = %s, etage = %s, capacite = %s, last_sync = NOW()
                        WHERE id_ecoledirecte = %s
                    """, (salle['nom'], salle.get('batiment'), salle.get('etage'),
                          salle.get('capacite'), salle['id']))
                else:
                    # Insérer une nouvelle salle
                    get_db("""
                        INSERT INTO ecoledirecte_salles 
                        (id_ecoledirecte, nom, batiment, etage, capacite)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (salle['id'], salle['nom'], salle.get('batiment'),
                          salle.get('etage'), salle.get('capacite')))
            
            return True
        except Exception as e:
            print(f"Erreur lors de la synchronisation des salles: {e}")
            return False
    
    def synchroniser_emploi_du_temps(self):
        """
        Synchronise l'emploi du temps avec la base de données locale
        """
        try:
            edt = self.get_emploi_du_temps()
            if not edt:
                return False
            
            # Créer une table pour l'emploi du temps si elle n'existe pas
            get_db("""
                CREATE TABLE IF NOT EXISTS ecoledirecte_emploi_du_temps (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    id_cours VARCHAR(50) NOT NULL UNIQUE,
                    matiere VARCHAR(255) NOT NULL,
                    professeur VARCHAR(255),
                    salle VARCHAR(100),
                    date_debut DATETIME NOT NULL,
                    date_fin DATETIME NOT NULL,
                    groupe VARCHAR(100),
                    last_sync DATETIME DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_id_cours (id_cours),
                    INDEX idx_date_debut (date_debut),
                    INDEX idx_date_fin (date_fin)
                )
            """)
            
            # Mettre à jour ou insérer les cours
            for cours in edt['data']:
                existing = get_db(
                    "SELECT id FROM ecoledirecte_emploi_du_temps WHERE id_cours = %s",
                    (cours['id'],)
                )
                
                if existing:
                    # Mettre à jour le cours existant
                    get_db("""
                        UPDATE ecoledirecte_emploi_du_temps 
                        SET matiere = %s, professeur = %s, salle = %s,
                            date_debut = %s, date_fin = %s, groupe = %s,
                            last_sync = NOW()
                        WHERE id_cours = %s
                    """, (cours['matiere'], cours.get('professeur'), cours.get('salle'),
                          cours['debut'], cours['fin'], cours.get('groupe'), cours['id']))
                else:
                    # Insérer un nouveau cours
                    get_db("""
                        INSERT INTO ecoledirecte_emploi_du_temps 
                        (id_cours, matiere, professeur, salle, date_debut, date_fin, groupe)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (cours['id'], cours['matiere'], cours.get('professeur'),
                          cours.get('salle'), cours['debut'], cours['fin'],
                          cours.get('groupe')))
            
            return True
        except Exception as e:
            print(f"Erreur lors de la synchronisation de l'emploi du temps: {e}")
            return False
