def addtiqué(by, descipion):
    import mysql.connector
    import random
    # Connexion à la base de données
    db = mysql.connector.connect(
        host="localhost",
        database="database"
    )

    # Créer un curseur pour effectuer des opérations SQL
    cur = db.cursor()

    # Requête SQL pour insérer une ligne dans la table "person"
    sql = "INSERT INTO tiqué (ID, by, descipition) VALUES (%s, %s, %s)"

    # Valeurs à insérer dans la requête SQL
    values = (random.randint(10000,99999), by, descipion)

    # Exécution de la requête SQL
    cur.execute(sql, values)

    # Valider les modifications
    db.commit()

    # Afficher le nombre de lignes insérées
    print(cur.rowcount, "ligne insérée.")


addtiqué('test','test')