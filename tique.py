import sqlite3
import datetime
import secrets
def create_tiqué(ID_user, titre, description, gravité, tags):
    conn = sqlite3.connect('database.db')  # Updated connection string
    cursor = conn.cursor()
    ID_tiqué =str(secrets.token_urlsafe(16))
    data = {
        'ID_user': ID_user,
        'ID_tiqué': ID_tiqué,
        'date_open': str(datetime.date.today()),
        'titre': titre,
        'descipition': description,
        'gavite': gravité,
        'tags': tags
    }
    cursor.execute("""INSERT INTO tiqué(ID_tiqué, ID_user, date_open, titre, descipition, gavite, tag) 
                    VALUES(:ID_tiqué, :ID_user, :date_open, :titre, :descipition, :gavite, :tags)""", data)
    conn.commit()
    conn.close()
    print("Tiqué ajouté avec succès!")
    return ID_tiqué

def close_tiqué(ID_tiqué):
    conn = sqlite3.connect('database.db')  # Updated connection string
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tiqué WHERE ID_tiqué=?", (ID_tiqué,))
    existing_tiqué = cursor.fetchone()
    if existing_tiqué:
        cursor.execute("""UPDATE tiqué SET open=0, date_close=? WHERE ID_tiqué=?""", (datetime.date.today(), ID_tiqué))
        conn.commit()
        conn.close()
        print("Tiqué close avec succès!")
        return True
    else:
        print("Pas de tiqué associé à cet ID.")
        raise ValueError("Pas de tiqué associé à cet ID.")
        return False

# test
# create_tiqué(1515151515,"Tiqué test", "Description test", 1, "tag1, tag2")
# close_tiqué(input("ID_tiqué"))