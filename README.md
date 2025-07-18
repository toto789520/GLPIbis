# 🎯 GLPIbis - Votre Meilleur Ami pour la Gestion IT ! 

Bienvenue dans l'aventure GLPIbis ! 🚀 Une application inspirée de GLPI mais avec une touche de modernité et de simplicité.

## 🌟 C'est quoi ce truc ?

GLPIbis est votre couteau suisse de la gestion IT ! Imaginez un majordome numérique qui :
- 🎫 Gère vos tickets comme un chef
- 📦 Surveille votre inventaire 
- 🔐 Protège vos données comme Fort Knox
- 📱 Propose une interface aussi intuitive qu'un réseau social

## 🔧 Installation (Spoiler : C'est super simple !)

1. **Clone le repo comme un pro :**
   ```bash
   git clone https://github.com/votre-compte/GLPIbis.git
   cd GLPIbis
   ```

2. **Installe les dépendances (on a tous besoin d'amis) :**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure ton environnement (comme ta chambre, mais en mieux) :**
   - Copie le fichier `.env.example` vers `.env`
   - Remplis les infos (promis, on ne demande pas ton mot de passe Netflix)

4. **Initialise la base de données :**
   ```bash
   python migrate_databases.py
   ```

5. **Lance l'application et deviens un héros :**
   ```bash
   python app.py
   ```

## 🗂️ Structure du Projet (Pour les Curieux)

```
GLPIbis/
├── 🏠 app.py              # Le chef d'orchestre
├── 📁 routes/            # Où la magie des URLs opère
├── 🎨 static/            # Les beaux atours de l'app
├── 📝 templates/         # Les squelettes HTML
├── 🔧 utils/             # La boîte à outils
└── 📦 inventory/         # Où on compte les petits moutons (matériels)
```

## 🚀 Fonctionnalités Principales

### 1. 🎫 Gestion des Tickets
- Création facile (même votre grand-mère peut le faire)
- Suivi en temps réel
- Commentaires et interactions
- Priorisation intelligente

### 2. 📦 Inventaire
- Gestion du matériel avec codes QR
- Suivi des emprunts/retours
- Historique complet
- Alertes de maintenance

### 3. 👥 Gestion des Utilisateurs
- Authentification sécurisée
- Gestion des rôles (comme dans Game of Thrones, mais en plus pacifique)
- Profils personnalisables

### 4. 📊 Rapports et Statistiques
- Tableaux de bord intuitifs
- Statistiques en temps réel
- Exports au format Excel (pour faire plaisir au chef)

## 🔧 API pour les Devs Cool

Base URL : `http://votre-serveur:port/api/v1`

Exemples d'endpoints :
```javascript
GET    /api/tickets     // Liste des tickets
POST   /api/inventory   // Ajouter du matériel
PUT    /api/users/:id   // Mettre à jour un utilisateur
```

## 🤝 Contribution (On recrute des héros!)

1. Fork le projet (comme une pizza, mais en code)
2. Crée ta branche (`git checkout -b feature/TrucCool`)
3. Commit tes changements (`git commit -m 'Ajout d'un truc cool'`)
4. Push vers la branche (`git push origin feature/TrucCool`)
5. Ouvre une Pull Request et croise les doigts ! 🤞

## 🐛 Résolution de Problèmes

### L'app ne démarre pas ?
- T'as bien installé les dépendances ? (`pip install -r requirements.txt`)
- Le fichier `.env` est bien configuré ?
- Tu as sacrifié un cookie aux dieux du code ?

### La base de données fait des siennes ?
```bash
python debug_db.py --fix-my-life
```

## 📝 Logs (Pour les Détectives)

Les logs sont stockés dans `logs/glpibis.log`. Si tu vois des 🔴, c'est pas bon signe !

## ⚡ Mode SOS 

En cas de pépin :
1. Active le mode SOS : `python app.py --sos`
2. Prie tous les dieux connus
3. Contacte l'équipe (on ne dort jamais)

## 🎉 Versions

- v1.0.0 : La base solide
- v1.1.0 : Les trucs cool
- v2.0.0 : Le futur (bientôt™)

## 📜 License

Fait avec ❤️ par des devs qui ne dorment pas. Utilisez-le comme vous voulez (mais citez-nous quand même) !
