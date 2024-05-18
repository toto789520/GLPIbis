import test_db
import sqlite3
import hashlib
import datetime
from db import adduser
from db import verify_password
from db import delete_user
def test_adduser(db):
    by = "test_user"
    age = 25
    tel = "1234567890"
    email = "test_user@example.com"
    password = "test123"

    # Connect to the database
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    # Check if the user has been added
    cursor.execute("SELECT * FROM USEUR WHERE email=?", (email,))
    new_user = cursor.fetchone()
    print("************************",new_user[1],"  ",str(datetime.date.today()))
    print("************************",new_user[2],"  ",by)
    print("************************",new_user[3],"  ",age)
    assert new_user is not None, "User not added to the database"
    assert new_user[1] == str(datetime.date.today()), "Incorrect date of creation"  # Resolved the warning message
    assert new_user[2] == age, "Incorrect age"
    assert new_user[3] == by, "Incorrect name"
    assert new_user[4] == tel, "Incorrect phone number"
    assert new_user[5] == email, "Incorrect email"
    assert new_user[6] == hashlib.md5((password + new_user[0]).encode()).hexdigest(), "Incorrect hashed password"

    # Close the database connection
    conn.close()


def test_verify_password(db):
    by = "test_user"
    age = 25
    tel = "1234567890"
    email = "test_user@example.com"
    password = "test123"

    # Connect to the database
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    # Verify the password
    assert verify_password(password, email) == True, "Incorrect password verification"

    # Close the database connection
    conn.close()


def test_delete_user(db):
    by = "test_user"
    age = 25
    tel = "1234567890"
    email = "test_user@example.com"
    password = "test123"

    # Connect to the database
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    # Delete the user
    assert delete_user(email) == True, "User not deleted from the database"

    # Check if the user has been deleted
    cursor.execute("SELECT * FROM USEUR WHERE email=?", (email,))
    deleted_user = cursor.fetchone()
    assert deleted_user is None, "User still exists in the database"

    # Close the database connection
    conn.close()


test_adduser("database.db")