import sqlite3
import os

def initialize_database():
    base_dir = os.path.dirname(__file__)
    db_dir = os.path.join(base_dir, "db")
    db_path = os.path.join(db_dir, "clubbot.db")

    # ✅ Make sure folder exists
    os.makedirs(db_dir, exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Contacts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            name TEXT,
            whatsapp TEXT UNIQUE,
            birthday TEXT,
            instagram TEXT,
            rating INTEGER,
            last_club TEXT,
            visit_date TEXT,
            category TEXT,
            recent_visit TEXT,
            club_visits INTEGER
        );
    """)

    # Messages table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            content TEXT NOT NULL
        );
    """)

    # Campaign reports
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS campaign_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_id INTEGER,
            message TEXT NOT NULL,
            status TEXT,
            sent_date TEXT,
            FOREIGN KEY(contact_id) REFERENCES contacts(rowid)
        );
    """)

    # Groups
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive'))
        );
    """)

    # Contact-Group map
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contact_group_map (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contact_id INTEGER NOT NULL,
            group_id INTEGER NOT NULL,
            FOREIGN KEY (contact_id) REFERENCES contacts(rowid),
            FOREIGN KEY (group_id) REFERENCES groups(id),
            UNIQUE(contact_id, group_id)
        );
    """)

    conn.commit()
    conn.close()
    print("✅ Database schema initialized.")

if __name__ == "__main__":
    initialize_database()
