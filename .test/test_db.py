import test_db
import sqlite3
import hashlib
import datetime
from db import adduser
from db import verify_password
from db import delete_user
from db import modify_user
def hard_delete_user(ID_user, db):
    conn = sqlite3.connect(db)  # Updated connection string
    cursor = conn.cursor()
    cursor.execute("DELETE FROM USEUR WHERE ID=?", (ID_user,))
    conn.commit()
    cursor.execute("DELETE FROM stsate WHERE ID=?", (ID_user,))
    conn.commit()
    conn.close()

def test_adduser(db):
    by = "test_user"
    age = 25
    tel = "1234567890"
    email = "test_user@example.com"
    password = "test123"

    # Connect to the database
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    # Add the user to the database
    adduser(by, age, tel, email, password)
    conn.commit()
    
    # Check if the user has been added
    cursor.execute("SELECT * FROM USEUR WHERE email=?", (email,))
    new_user = cursor.fetchone()
    assert new_user is not None, "User not added to the database"
    assert new_user[1] == str(datetime.date.today()), "Incorrect date of creation"  # Resolved the warning message
    assert new_user[2] == age, "Incorrect age"
    assert new_user[3] == by, "Incorrect name"
    assert new_user[4] == tel, "Incorrect phone number"
    assert new_user[5] == email, "Incorrect email"
    assert new_user[6] == hashlib.md5((password + new_user[0]).encode()).hexdigest(), "Incorrect hashed password"

    # Close the database connection
    conn.close()

    # Delete the user from the database
    hard_delete_user(new_user[0], db)


def test_verify_password(db):
    by = "test_user"
    age = 25
    tel = "1234567890"
    email = "test_user@example.com"
    password = "test123"

    #adduser(by, age, tel, email, password)
    adduser(by, age, tel, email, password)

    # Connect to the database
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    # récupérer l'ID de l'utilisateur
    cursor.execute("SELECT ID FROM USEUR WHERE email=?", (email,))
    new_user = cursor.fetchone()
    assert new_user is not None, "User not added to the database"
    ID_user = new_user[0]


    # Verify the password
    assert verify_password(password, email) == new_user[0], "Incorrect password verification"

    # Close the database connection
    conn.close()

    # Delete the user from the database
    hard_delete_user(ID_user, db)


def test_delete_user(db):
    by = "test_user"
    age = 25
    tel = "1234567890"
    email = "test_user@example.com"
    password = "test123"

    #adduser(by, age, tel, email, password)
    adduser(by, age, tel, email, password)

    # Connect to the database
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    # récupérer l'ID de l'utilisateur
    cursor.execute("SELECT ID FROM USEUR WHERE email=?", (email,))
    new_user = cursor.fetchone()
    assert new_user is not None, "User not added to the database"
    ID_user = new_user[0]

    # Delete the user
    assert delete_user(email, hashlib.md5((password + new_user[0]).encode()).hexdigest()) == True, "User not deleted from the database"

    # Check if the user has been deleted
    cursor.execute("SELECT * FROM USEUR WHERE email=?", (email,))
    deleted_user = cursor.fetchone()
    assert deleted_user is None, "User still exists in the database"

    # Close the database connection
    conn.close()

    hard_delete_user(ID_user, db)

def test_modify_user_success(db):
    # Assuming the database is already populated with a user
    old_password = "old_password"
    new_password = "new_password"
    new_name = "new_name"
    old_name = "old_name"
    new_age = 22
    old_age = 25
    new_tel = "1234567890"
    old_tel = "0987654321"
    new_email = "new_email@example.com"
    old_email = "old_email@example.com"

    #adduser(by, age, tel, email, password)
    adduser(old_name, old_age, old_tel, old_email, old_password)

    # Connect to the database
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    # récupérer l'ID de l'utilisateur
    cursor.execute("SELECT ID FROM USEUR WHERE email=?", (old_email,))
    new_user = cursor.fetchone()
    assert new_user is not None, "User not added to the database"
    ID_user = new_user[0]

    # Call the modify_user function
    result = modify_user(ID_user, new_name, new_age, new_tel, old_email, new_email, old_password, new_password)

    # Assert that the function returns True and the user's details have been updated
    assert result == True
    # Add more assertions to check if the user's details have been updated correctly
    hard_delete_user(ID_user, db)

def test_modify_user_wrong_old_password(db):
    # Assuming the database is already populated with a user
    wrong_password = "wrong_password"
    new_password = "new_password"
    old_password = "old_password"
    new_name = "new_name"
    old_name = "old_name"
    new_age = 22
    old_age = 25
    new_tel = "1234567890"
    old_tel = "0987654321"
    new_email = "new_email@example.com"
    old_email = "old_email@example.com"

    #adduser(by, age, tel, email, password)
    adduser(old_name, old_age, old_tel, old_email, old_password)

    # Connect to the database
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    # récupérer l'ID de l'utilisateur
    cursor.execute("SELECT ID FROM USEUR WHERE email=?", (old_email,))
    new_user = cursor.fetchone()
    assert new_user is not None, "User not added to the database"
    ID_user = new_user[0]

    # Call the modify_user function
    try:
        result = modify_user(ID_user, new_name, new_age, new_tel, old_email, new_email, wrong_password, new_password)
    except ValueError:
        result = False

    # Assert that the function returns False and the user's details have not been updated
    assert result != True
    # Add more assertions to check if the user's details have not been updated
    hard_delete_user(ID_user, db)