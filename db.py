import mysql.connector
import mysql.connector
from argon2 import PasswordHasher
import datetime
import secrets
from email_validator import validate_email, EmailNotValidError
import json
from alive_progress import alive_bar

with alive_bar(0) as bar:

    def get_config(parametre):
        try:
            # Ouvre le fichier de configuration en mode lecture
            with open('conf.conf', 'r') as file:
                config_data = json.load(file)  # Charge le contenu JSON dans un dictionnaire
                return config_data.get(parametre, None)  # Retourne la valeur associée au paramètre ou None si le paramètre n'existe pas
        except FileNotFoundError:
            print("Le fichier de configuration n'a pas été trouvé.")
            return None
        except json.JSONDecodeError:
            print("Erreur de décodage JSON dans le fichier de configuration.")
            return None


    def get_db(requete, data=""):
        mydb = mysql.connector.connect(
            host=get_config("IP_db"),
            user=get_config("user_db"),
            password=get_config("password_db"),
            database=get_config("name_db"),
        )
        mycursor = mydb.cursor()
        print(requete)
        print(data)
        mycursor.execute(requete, data)
        
        if requete.strip().upper().startswith("SELECT"):
            results = mycursor.fetchall()
        else:
            mydb.commit()
            results = mycursor.rowcount
        
        mycursor.close()
        mydb.close()
        return results


    def adduser(by, age, tel, email, password): 
        ID = str(secrets.token_urlsafe(16))
        passw = (password + ID)
        hashed_password = hashlib.md5(passw.encode())
        data = {
            'ID': ID,
            'dete_de_creation': str(datetime.date.today()),
            'name': by,
            'age' : age,
            'tel' : tel,
            'email': email,
            'hashed_password': str(hashed_password.hexdigest())
        }
        existing_user = get_db(f"""SELECT * FROM USEUR WHERE email='{email}'""")
        if existing_user:
            print("L'e-mail existe déjà dans la base de données.")
            raise ValueError("L'e-mail existe déjà dans la base de données.")
        
        try:
            valid = validate_email(email)
        except EmailNotValidError:
            raise ValueError("Email Incorrect")
        
        # Insertion dans la table USEUR
        get_db("""INSERT INTO USEUR (ID, dete_de_creation, name, age, tel, email, hashed_password) 
                VALUES (%(ID)s, %(dete_de_creation)s, %(name)s, %(age)s, %(tel)s, %(email)s, %(hashed_password)s)""", data)
        
        # Insertion dans la table state
        get_db("""INSERT INTO state (id_user, tiqué_créer, tiqué_partisipé, comm) 
                VALUES (%(ID)s, 0, 0, 0)""", {'ID': ID})
        
        print("Utilisateur ajouté avec succès!")
        return ID  
    

    def adduser(by, age, tel, email, password): 
        ID = str(secrets.token_urlsafe(16))
        passw = (password + ID)
        hashed_password = hashlib.md5(passw.encode())
        data = {
            'ID': ID,
            'dete_de_creation': str(datetime.date.today()),
            'name': by,
            'age' : age,
            'tel' : tel,
            'email': email,
            'hashed_password': str(hashed_password.hexdigest())
        }
        existing_user = get_db(f"""SELECT * FROM USEUR WHERE email='{email}'""")
        if existing_user:
            print("L'e-mail existe déjà dans la base de données.")
            raise ValueError("L'e-mail existe déjà dans la base de données.")
        
        try:
            valid = validate_email(email)
        except EmailNotValidError:
            raise ValueError("Email Incorrect")
        
        # Insertion dans la table USEUR
        get_db("""INSERT INTO USEUR (ID, dete_de_creation, name, age, tel, email, hashed_password) 
                VALUES (%(ID)s, %(dete_de_creation)s, %(name)s, %(age)s, %(tel)s, %(email)s, %(hashed_password)s)""", data)
        
        # Insertion dans la table state
        get_db("""INSERT INTO state (id_user, tiqué_créer, tiqué_partisipé, comm) 
                VALUES (%(ID)s, 0, 0, 0)""", {'ID': ID})
        
        print("Utilisateur ajouté avec succès!")
        return ID  



    def verify_password(password, email):
        existing_user= get_db(f"SELECT hashed_password FROM USEUR WHERE email='{email}'")
        ID_user = get_db(f"SELECT ID FROM USEUR WHERE email='{email}'")
        if existing_user:
            ph = PasswordHasher()
            if ph.verify(existing_user[0][0], password + ID_user[0][0]):
                return str(ID_user[0][0])
            else:
                print("Tentative de connexion avec un email privé avec un mot de passe. : " + str(email))
                raise ValueError("Mot de passe ou adresse e-mail inexacte")
        else:
            print("tentative de connexion avec email :" + str(email))
            raise ValueError("l'utilisateur est introuvable")


    def delete_user(email, password):
        verify_password(password, email)
        existing_user=get_db(f"SELECT * FROM USEUR WHERE email='{email}'")


        if existing_user:
            get_db(f"DELETE FROM USEUR WHERE email='{email}'")
            get_db(f"DELETE FROM stsate WHERE id_user='{existing_user[0]}'")
            print("Utilisateur supprimé avec succès!")
            return True
        else:
            print("Pas de compte associé à cet e-mail.")
            return False

    def modify_user(ID_user, by, age, tel, old_email, now_email, old_password, now_password):
        existing_user = get_db(f"SELECT * FROM USEUR WHERE email='{old_email}'")
        print(existing_user)
        if existing_user is None:
            print("L'e-mail existe pas dans la base de données.")
            raise ValueError("L'e-mail existe pas dans la base de données.")
            return False


        # Verify the old password and get the user ID
        if ID_user == verify_password(old_password, old_email):
            # Hash the new password with the user ID
            ph = PasswordHasher()
            now_password_hashed = ph.hash(now_password + ID_user)
            
            # Prepare data for update
            data = (by, age, tel, now_email, now_password_hashed, ID_user)
            
            # Execute the update statement
            get_db("""UPDATE USEUR SET name=?, age=?, tel=?, email=?, hashed_password=? WHERE ID=?""", data)
            
            # Commit the transaction
            print("Utilisateur mis à jour avec succès!")
            return True
        elif ID_user != verify_password(old_password, old_email):
            print("Mauvais mot de passe.")
            raise ValueError("Mauvais mot de passe.")
            return False
        # Close the connection

    def who(ID):
        existing_user= get_db("SELECT * FROM USEUR WHERE ID=%s", (str(ID),))
        print(existing_user)
        print(str(ID)+" aficher")
        if existing_user is None:
            print("ID existe pas dans la base de données.")
            raise ValueError("ID existe pas dans la base de données.")
        else:
            return existing_user[0][3]
        
    def state_add_user(type, ID_user, ID_tiqué):
        print("state user")
        if type == "tiqué_créer" or "post_comm":
            try:
                user = who(ID_user)
                if user is None:
                    raise ValueError("id user erreur")
            except ValueError as e:
                print(e)
                return ValueError(e)

            if type == "tiqué_créer":
                user = get_db(f"SELECT * FROM stsate WHERE id_user=?", (ID_user,))
                user = list(user)
                user[1] = int(user[1])+1
                user = tuple(user)
                get_db("UPDATE stsate SET id_user=?, tiqué_créer=?, tiqué_partisipé=?, comm=?", user)
                return True
            elif type == "post_comm":
                print("post_comm")
                existing_tiqué=get_db(f"SELECT * FROM {ID_tiqué} WHERE ID_user=?", (ID_user,))
                if existing_tiqué:
                    user=get_db("SELECT * FROM stsate WHERE id_user=?", (ID_user,))
                    user = list(user)
                    user[3] = int(user[3]) +1
                    user = tuple(user)
                    get_db("""UPDATE stsate SET id_user=?, tiqué_créer=?, tiqué_partisipé=?, comm=?""", user)
                    return True
                else:
                    user = get_db("SELECT * FROM stsate WHERE id_user=?", (ID_user,))
                    user = list(user)
                    user[2] = int(user[2]) +1
                    user[3] = int(user[3]) +1
                    user = tuple(user)
                    get_db("""UPDATE stsate SET id_user=?, tiqué_créer=?, tiqué_partisipé=?, comm=?""", user)
                    return True
        else:
            print("Type invalide.")
            return False
                
    def tiqué_type() :
        tickets=get_db("SELECT * FROM tiqué_type") 
        return tickets

    def ader_type() :
        tickets =get_db("SELECT * FROM arder") 
        return tickets


    # Example usage:
    # adduser("coucou", 16, "0643744076", "opm852159@gmail.com", "test123")
    # print(verify_password("test123", "opm852159@gmail.com"))
    # delete_user("opm852159@gmail.com", "test123")
