import string
import datetime
import secrets
from db import state_add_user, get_db

# Get the current date
current_date = datetime.date.today()

# Get the current date and time
current_datetime = datetime.datetime.now()

def generate_valid_table_name(length=16):
    valid_chars = string.ascii_letters
    return ''.join(secrets.choice(valid_chars) for _ in range(length))

def create_tiqué(ID_user, titre, description, gravité, tags):
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
    get_db("""INSERT INTO tiqué(ID_tiqué, ID_user, date_open, titre, descipition, gavite, tag) 
                    VALUES(:ID_tiqué, :ID_user, :date_open, :titre, :descipition, :gavite, :tags)""", data)
    get_db(f"""CREATE TABLE {ID_tiqué}(ID_user NUMERIC, date TEXT, hour TEXT, commenter TEXT);""")
    state_add_user("tiqué_créer", ID_user, ID_tiqué)
    print("Tiqué ajouté avec succès!")
    return ID_tiqué

def close_tiqué(ID_tiqué, ID_user):
    existing_tiqué = get_db("SELECT * FROM tiqué WHERE ID_user=?", (ID_user,))
    if existing_tiqué:
        existing_tiqué = get_db(f"SELECT * FROM {ID_tiqué} WHERE ID_user=?", (ID_user,))
        if existing_tiqué:
            get_db("""UPDATE tiqué SET open=0, date_close=? WHERE ID_tiqué=?""", (datetime.date.today(), ID_tiqué))
            print("Tiqué fermé avec succès!")
            return True
        else:
            print("Vous n'avez jamais mis de commentaire sur le tiqué")
            raise LookupError("Vous n'avez jamais mis de commentaire sur le tiqué")
    else:
        print("Pas de tiqué associé à cet ID.")
        raise ValueError("Pas de tiqué associé à cet ID.")
        return False

def now_comment(ID_tiqué, ID_user, commenter):
    current_datetime = datetime.datetime.now()
    state_add_user("post_comm", ID_user, ID_tiqué)
    data = {
        'ID_user': ID_user,
        'date': str(datetime.date.today()),  # Current date
        'hour': current_datetime.time().strftime("%H:%M:%S"),  # Current time
        'commenter': commenter
    }
    get_db(f"""INSERT INTO {ID_tiqué}(ID_user, date, hour, commenter) VALUES(:ID_user, :date, :hour, :commenter)""", data)

def list_tiqué(filter_value=None):
    if filter_value == "all":
        tickets = get_db("SELECT * FROM tiqué")
    elif filter_value:
        tickets = get_db(f"SELECT * FROM tiqué WHERE tag = '{filter_value}'")
    else:
        tickets = get_db("SELECT * FROM tiqué")

    return tickets

def get_info_tiqué(id_tiqué):
    tickets = get_db(f"SELECT * FROM tiqué WHERE ID_tiqué = '{id_tiqué}'")
    return tickets

def get_info_tiqué_comment(id_tiqué):
    comment = get_db(f"SELECT * FROM {id_tiqué}")
    return comment

# test
# create_tiqué(1515151515,"Tiqué test", "Description test", 1, "tag1, tag2")
# now_comment("uosTWpOvqBKHpKlB", 1515151515, "coucou")
# now_comment("uosTWpOvqBKHpKlB", 1515151515, "help")
# close_tiqué(input("ID_tiqué"))
