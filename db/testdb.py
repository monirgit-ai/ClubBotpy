import sqlite3

conn = sqlite3.connect("clubbot.db")
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
conn.close()

print("Tables found:", tables)
