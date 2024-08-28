import string
import sqlite3
import datetime
import secrets
from db import state_add_user
import datetime

# Get the current date
current_date = datetime.date.today()

# Get the current date and time
current_datetime = datetime.datetime.now()
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
    state_add_user("tiqué_créer",ID_user,ID_tiqué)
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
            conn = sqlite3.connect('database.db')  # Updated connection string
            cursor = conn.cursor()
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
    current_datetime = datetime.datetime.now()
    state_add_user("post_comm",ID_user,ID_tiqué)
    data = {
        'ID_user': ID_user,
        'date': str(datetime.date.today()),  # Current date
        'hour': current_datetime.time().strftime("%H:%M:%S"),  # Current time
        'commenter': commenter
    }
    conn.execute(f"""INSERT INTO {ID_tiqué}(ID_user, date, hour, commenter) VALUES(:ID_user, :date, :hour, :commenter)""", data)
    conn.commit()
    conn.close()


def list_tiqué(filter_value=None):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    if filter_value == "all":
        cursor.execute("SELECT * FROM tiqué")
    elif filter_value!="all":
        cursor.execute("SELECT * FROM tiqué WHERE tag = ?", (filter_value,))
    else:
        cursor.execute("SELECT * FROM tiqué")
        
    tickets = cursor.fetchall()
    conn.close()

    return tickets

def get_info_tiqué(id_tiqué):
    conn = sqlite3.connect('database.db')  # Connect to the database.
    cursor = conn.cursor()  # Create a cursor object to execute SQL queries.

    # Execute a SQL query to select all columns from the 'tiqué' table where the 'ID_tiqué' column matches the provided 'id_tiqué'.
    cursor.execute("SELECT * FROM tiqué WHERE ID_tiqué = ?", (id_tiqué,))

    # Fetch all the rows returned by the query and store them in the 'tickets' variable.
    tickets = cursor.fetchall()

    # Close the database connection.
    conn.close()

    # Return the list of tuples containing the information about the ticket.
    return tickets

def get_info_tiqué_comment(id_tiqué):
    conn = sqlite3.connect('comm.db')  # Updated connection string
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {id_tiqué}")
    comment = cursor.fetchall()
    conn.close()
    return comment

# test
# create_tiqué(1515151515,"Tiqué test", "Description test", 1, "tag1, tag2")
# now_comment("uosTWpOvqBKHpKlB", 1515151515, "coucou")
# now_comment("uosTWpOvqBKHpKlB", 1515151515, "help")
# close_tiqué(input("ID_tiqué"))
print(list_tiqué())
