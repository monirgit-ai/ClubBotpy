import sqlite3

def init_db():
    conn = sqlite3.connect("clubbot.db")
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            whatsapp TEXT NOT NULL UNIQUE,
            birthday TEXT,
            last_visit TEXT,
            rating TEXT,
            category TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            content TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS campaign_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_id INTEGER,
            message TEXT NOT NULL,
            status TEXT,
            sent_date TEXT,
            FOREIGN KEY(contact_id) REFERENCES contacts(id)
        )
    ''')

    conn.commit()
    conn.close()
