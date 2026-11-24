
import mysql.connector
from werkzeug.security import generate_password_hash
from getpass import getpass

connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="academic_timetable"
)

cursor = connection.cursor()

print("CREATE ADMINISTRATOR ACCOUNT")

name = input("Enter your full name: ").strip()
email = input("Enter your email: ").strip().lower()
password = getpass("Create password: ")
confirm = getpass("Confirm password: ")

if not name or not email or not password:
    print("All fields are required.")

elif password != confirm:
    print("Passwords do not match.")

else:
    try:
        password_hash = generate_password_hash(password)

        cursor.execute("""
            INSERT INTO users
            (full_name, email, password_hash, role, department)
            VALUES (%s, %s, %s, %s, %s)
        """, (name, email, password_hash,
              "Administrator", "Administration"))

        connection.commit()
        print("Administrator account created successfully!")

    except mysql.connector.Error as error:
        connection.rollback()
        print("Account creation failed:", error)

cursor.close()
connection.close()
