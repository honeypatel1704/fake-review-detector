import sqlite3
import os

# Get absolute path of database inside this folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "users.db")

print("Database path:", DB_PATH)

# Connect to DB
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("SELECT * FROM users")
rows = cursor.fetchall()

print("\nStored Users:\n")
for row in rows:
    print(row)

conn.close()
