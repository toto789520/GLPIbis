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
        'dete_de_creation': str(datetime.date.today()),
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
                    VALUES(:ID, :dete_de_creation, :name, :age, :tel, :email, :hashed_password)""", data)
    conn.commit()
    cursor.execute("INSERT INTO stsate(id_user, tiqué_créer, tiqué_partisipé, comm) VALUES (?, 0, 0, 0)", (ID,))
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
            return str(ID_user[0])
        else:
            return False
    else:
        return False


def delete_user(email, password):
    conn = sqlite3.connect('database.db')  # Updated connection string
    cursor = conn.cursor()
    verify_password(password, email)
    cursor.execute("SELECT * FROM USEUR WHERE email=?", (email,))
    existing_user = cursor.fetchone()

    if existing_user:
        cursor.execute("DELETE FROM USEUR WHERE email=?", (email,))
        conn.commit()
        cursor.execute("DELETE FROM stsate WHERE id_user=?", (existing_user[0],))
        conn.commit()
        conn.close()
        print("Utilisateur supprimé avec succès!")
        return True
    else:
        print("Pas de compte associé à cet e-mail.")
        return False

def modify_user(ID_user, by, age, tel, old_email, now_email, old_password, now_password):
    conn = sqlite3.connect('database.db')  # Updated connection string
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM USEUR WHERE email=?", (old_email,))
    existing_user = cursor.fetchone()
    print(existing_user)
    if existing_user is None:
        print("L'e-mail existe pas dans la base de données.")
        raise ValueError("L'e-mail existe pas dans la base de données.")
        return False


    # Verify the old password and get the user ID
    if ID_user == verify_password(old_password, old_email):
        # Hash the new password with the user ID
        now_password_hashed = hashlib.md5((now_password + ID_user).encode()).hexdigest()
        
        # Prepare data for update
        data = (by, age, tel, now_email, now_password_hashed, ID_user)
        
        # Execute the update statement
        cursor.execute("""UPDATE USEUR SET name=?, age=?, tel=?, email=?, hashed_password=? WHERE ID=?""", data)
        
        # Commit the transaction
        conn.commit()
        print("Utilisateur mis à jour avec succès!")
        return True
    elif ID_user != verify_password(old_password, old_email):
        print("Mauvais mot de passe.")
        raise ValueError("Mauvais mot de passe.")
        return False
    # Close the connection
    conn.close()


# Example usage:
# adduser("coucou", 16, "0643744076", "opm852159@gmail.com", "test123")
# print(verify_password("test123", "opm852159@gmail.com"))
# delete_user("opm852159@gmail.com", "test123")
