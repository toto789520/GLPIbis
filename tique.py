import string
import sqlite3
import datetime
import secrets

def generate_valid_table_name(length=16):
    valid_chars = string.ascii_letters
    return ''.join(secrets.choice(valid_chars) for _ in range(length))

def create_tiqué(ID_user, titre, description, gravité, tags):
    conn = sqlite3.connect('database.db')  # Updated connection string
    cursor = conn.cursor()
    ID_tiqué = generate_valid_table_name(16)
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
    conn = sqlite3.connect('comm.db')  # Updated connection string
    cursor = conn.cursor()
    cursor.execute(f"""CREATE TABLE {ID_tiqué}(ID_user NUMERIC, date TEXT, hour TEXT, commenter TEXT);""")
    conn.commit()
    conn.close()
    print("Tiqué ajouté avec succès!")
    return ID_tiqué

def close_tiqué(ID_tiqué, ID_user):
    conn = sqlite3.connect('database.db')  # Updated connection string
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tiqué WHERE ID_user=?", (ID_user,))
    existing_tiqué = cursor.fetchone()
    if existing_tiqué:
        conn.close
        conn = sqlite3.connect('comm.db')  # Updated connection string
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {ID_tiqué} WHERE ID_user=?", (ID_user,))
        existing_tiqué = cursor.fetchone()
        if existing_tiqué :
            cursor.execute("""UPDATE tiqué SET open=0, date_close=? WHERE ID_tiqué=?""", (datetime.date.today(), ID_tiqué))
            conn.commit()
            conn.close()
            print("Tiqué close avec succès!")
            return True
        else :
            print("vous avez j'ameis mi de commenter sur le tiqué")
            raise LookupError("vous avez j'ameis mi de commenter sur le tiqué")
    else:
        print("Pas de tiqué associé à cet ID.")
        raise ValueError("Pas de tiqué associé à cet ID.")
        return False

def now_comment(ID_tiqué, ID_user, commenter):
    conn = sqlite3.connect('comm.db')  # Updated connection string
    cursor = conn.cursor()
    data = {
        'ID_user': ID_user,
        'date': str(datetime.date.today()),
        'hour': int(datetime.time()),
        'commenter': commenter
    }
    conn.execute(f"""INSERT INTO {ID_tiqué}(ID_user, date, hour, commenter) VALUES(?,?,?)""",data)
# test
# create_tiqué(1515151515,"Tiqué test", "Description test", 1, "tag1, tag2")
# close_tiqué(input("ID_tiqué"))
