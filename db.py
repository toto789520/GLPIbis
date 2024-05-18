import sqlite3
import hashlib
import datetime
import secrets
import os

def adduser(by, age, tel, email, password):
    path = os.path.dirname(os.path.abspath(__file__))
    db = os.path.join(path, 'database.db')
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    ID = str(secrets.token_urlsafe(16))
    passw = (password + ID)
    hashed_password = hashlib.md5(passw.encode())
    data = {
        'ID': ID,
        'dete_de_crétion': str(datetime.date.today()),
        'name': by,
        'age': age,
        'tel': tel,
        'email': email,
        'hashed_password': str(hashed_password.hexdigest())
    }

    cursor.execute("SELECT * FROM USEUR WHERE email=?", (email,))
    existing_user = cursor.fetchone()
    print(existing_user)
    if existing_user:
        print("L'e-mail existe déjà dans la base de données.")
        raise ValueError("L'e-mail existe déjà dans la base de données.")
        return False

    cursor.execute("""INSERT INTO USEUR(ID, dete_de_crétion, name, age, tel, email, hashed_password) 
                    VALUES(:ID, :dete_de_crétion, :name, :age, :tel, :email, :hashed_password)""", data)
    conn.commit()
    conn.close()
    print("Utilisateur ajouté avec succès!")
    return True


def verify_password(password, email):
    conn = sqlite3.connect('database.db')  # Updated connection string
    cursor = conn.cursor()
    cursor.execute("SELECT hashed_password FROM USEUR WHERE email=?", (email,))
    existing_user = cursor.fetchone()
    cursor.execute("SELECT ID FROM USEUR WHERE email=?", (email,))
    ID_user = cursor.fetchone()
    if existing_user:
        hashed_password = hashlib.md5((password + ID_user[0]).encode()).hexdigest()
        if hashed_password == existing_user[0]:
            print("Mot de passe correct.")
            return True
        else:
            print("Mot de passe incorrect.")
            return False
    else:
        print("Pas de compte associé à cet e-mail.")
        return False


def delete_user(email):
    conn = sqlite3.connect('database.db')  # Updated connection string
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM USEUR WHERE email=?", (email,))
    existing_user = cursor.fetchone()

    if existing_user:
        cursor.execute("DELETE FROM USEUR WHERE email=?", (email,))
        conn.commit()
        conn.close()
        print("Utilisateur supprimé avec succès!")
        return True
    else:
        print("Pas de compte associé à cet e-mail.")
        return False


# Example usage:
# adduser("coucou", 16, "0643744076", "opm852159@gmail.com", "test123")
# verify_password("test123", "opm852159@gmail.com")
# delete_user("test_user@example.com")
