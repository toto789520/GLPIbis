from db import get_db

def add_materiel(nom, categorie, sous_categorie, sous_sous_categorie):
    ID = generate_id(categorie, sous_categorie, sous_sous_categorie)
    data = {
        'Nom': nom,
        'catégorie': categorie,
        'ID': ID
    }
    get_db("""
        INSERT INTO materiel (Nom, catégorie, ID)
        VALUES (%(Nom)s, %(catégorie)s, %(ID)s)
    """, data)
    print("Matériel ajouté avec succès!")

def delete_materiel(ID):
    get_db("DELETE FROM materiel WHERE ID=%s", (ID,))
    print("Matériel supprimé avec succès!")

def generate_id(categorie, sous_categorie, sous_sous_categorie):
    return f"{categorie:02d}{sous_categorie:02d}{sous_sous_categorie:02d}"

def get_categories():
    return get_db("SELECT * FROM categories")

def get_sous_categories(categorie_id):
    return get_db("SELECT * FROM sous_categories WHERE categorie_id=%s", (categorie_id,))

def get_sous_sous_categories(sous_categorie_id):
    return get_db("SELECT * FROM sous_sous_categories WHERE sous_categorie_id=%s", (sous_categorie_id,))
