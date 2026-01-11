Table glpi_users
Cette table stocke toutes les informations relatives aux utilisateurs, qu'ils soient demandeurs ou techniciens.

Nom de la colonne	Type	Description
id	INT	Clé primaire unique, auto-incrémentée.
name	VARCHAR	Identifiant de connexion de l'utilisateur (doit être unique).
realname	VARCHAR	Nom de famille de l'utilisateur.
firstname	VARCHAR	Prénom de l'utilisateur.
password	VARCHAR	Le mot de passe de l'utilisateur, généralement hashé.
email	VARCHAR	Adresse e-mail de l'utilisateur, utilisée pour les notifications.
phone	VARCHAR	Numéro de téléphone principal.
phone2	VARCHAR	Numéro de téléphone secondaire.
is_active	TINYINT(1)	Détermine si le compte est actif (1) ou désactivé (0).
entities_id	INT	Lien vers l'entité à laquelle l'utilisateur est principalement rattaché. Fondamental pour la gestion multi-entités.
date_creation	TIMESTAMP	Date et heure de création de la fiche utilisateur.
date_mod	TIMESTAMP	Date et heure de la dernière modification de la fiche.
Table glpi_itilcategories
Cette table contient la liste des catégories utilisées pour classer les tickets.

Nom de la colonne	Type	Description
id	INT	Clé primaire unique, auto-incrémentée.
name	VARCHAR	Le nom de la catégorie (ex: "Problème d'impression").
completename	TEXT	Le chemin complet de la catégorie si elle est dans une arborescence (ex: "Matériel > Imprimante > Problème d'impression").
entities_id	INT	Lien vers l'entité à laquelle la catégorie appartient.
is_recursive	TINYINT(1)	Si 1, la catégorie est visible dans les sous-entités de l'entité définie par entities_id.
Table glpi_tickets
C'est la table centrale du module de suivi. Chaque ligne représente un ticket.

Nom de la colonne	Type	Description
id	INT	Clé primaire unique, auto-incrémentée.
name	VARCHAR	Le titre ou l'objet du ticket.
content	LONGTEXT	La description détaillée du problème ou de la demande.
status	INT	Le statut actuel du ticket. Valeurs communes : 1 (Nouveau), 2 (En cours), 5 (Résolu), 6 (Fermé).
type	TINYINT	Le type de ticket : 1 pour un Incident, 2 pour une Demande.
priority	INT	La priorité du ticket, sur une échelle de 1 (Basse) à 6 (Très Haute).
urgency	INT	Le niveau d'urgence, sur une échelle de 1 (Basse) à 5 (Très Haute).
impact	INT	L'impact du problème, sur une échelle de 1 (Faible) à 5 (Majeur).
itilcategories_id	INT	Lien (ID) vers la catégorie dans la table glpi_itilcategories.
entities_id	INT	Lien vers l'entité à laquelle ce ticket appartient.
users_id_recipient	INT	L'ID de l'utilisateur qui a créé le ticket (le demandeur initial).
date	DATETIME	Date et heure de création du ticket.
date_mod	DATETIME	Date et heure de la dernière modification du ticket.
solvedate	DATETIME	Date et heure à laquelle le ticket a été marqué comme résolu.
closedate	DATETIME	Date et heure à laquelle le ticket a été fermé.
Table glpi_tickets_users
Cette table de liaison (many-to-many) définit le rôle des utilisateurs sur un ticket.

Nom de la colonne	Type	Description
id	INT	Clé primaire unique, auto-incrémentée.
tickets_id	INT	L'ID du ticket concerné (clé étrangère vers glpi_tickets).
users_id	INT	L'ID de l'utilisateur concerné (clé étrangère vers glpi_users).
type	TINYINT	Le rôle de l'utilisateur pour ce ticket. 1 = Demandeur, 2 = Technicien assigné, 3 = Observateur.
use_notification	TINYINT(1)	Si 1, l'utilisateur recevra les notifications par e-mail pour ce ticket.
Table glpi_items_tickets
Cette table de liaison permet d'associer un ticket à un ou plusieurs éléments du parc (un ordinateur, une imprimante, etc.).

Nom de la colonne	Type	Description
id	INT	Clé primaire unique, auto-incrémentée.
tickets_id	INT	L'ID du ticket concerné.
itemtype	VARCHAR(100)	Le type d'objet. C'est le nom de la table de l'objet (ex: Computer, Monitor, Printer).
items_id	INT	L'ID de l'objet dans sa table respective. La combinaison (itemtype, items_id) est unique.
Table glpi_ticketfollowups
Contient tous les commentaires et les notes ajoutées par les utilisateurs ou les techniciens pour faire suivre un ticket.

Nom de la colonne	Type	Description
id	INT	Clé primaire unique, auto-incrémentée.
tickets_id	INT	L'ID du ticket auquel ce suivi est rattaché.
users_id	INT	L'ID de l'utilisateur qui a rédigé le suivi.
content	LONGTEXT	Le texte du commentaire/de la note.
date	DATETIME	Date et heure d'ajout du suivi.
is_private	TINYINT(1)	Si 1, le suivi n'est visible que par les techniciens. Si 0, il est visible par le demandeur.
Table glpi_tickettasks
Permet de découper la résolution d'un ticket en plusieurs tâches planifiées.

Nom de la colonne	Type	Description
id	INT	Clé primaire unique, auto-incrémentée.
tickets_id	INT	L'ID du ticket parent de la tâche.
users_id	INT	L'ID du technicien à qui la tâche est assignée.
content	LONGTEXT	La description de ce qui doit être fait dans la tâche.
state	INT	Le statut de la tâche. Valeurs communes : 1 (À faire), 2 (En cours), 3 (Fait).
date_creation	DATETIME	Date et heure de création de la tâche.
date	DATETIME	Date de planification ou de réalisation.
date_end	DATETIME	Date à laquelle la tâche a été terminée.