import sqlite3
import hashlib
import datetime
import secrets
def adduseur(by, age, tel, email, password):
    conn = sqlite3.connect('database.db')
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
        'tiqué_ouver': 0,  # Assuming this is a default value
        'hashed_password': str(hashed_password.hexdigest())
    }
    print(data)
    cursor.execute("SELECT * FROM USEUR WHERE email=?", (email,))
    existing_user = cursor.fetchone()


    if existing_user:
        print("L'e-mail existe déjà dans la base de données.")
        return 2
    cursor.close
    print("L'e-mail n'existe pas dans la base de données.")
    print(data)
    conn.execute("""INSERT INTO USEUR(ID, dete_de_crétion, name, age, tel, email, tiqué_ouver, hashed_password) 
                    VALUES(:ID, :dete_de_crétion, :name, :age, :tel, :email, :tiqué_ouver, :hashed_password)""", data)
    conn.close



def confrimepassword(password,pin):
    print("nan")




print(adduseur("test", 16, "0643744076", "opm852159@gmail.com", "test123"))