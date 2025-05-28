import sqlite3
import os

def list_tables():
    db_path = os.path.join(os.path.dirname(__file__), 'db', 'clubbot.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    print("📋 Tables in database:")
    for t in tables:
        print("-", t[0])

    conn.close()

if __name__ == "__main__":
    list_tables()
