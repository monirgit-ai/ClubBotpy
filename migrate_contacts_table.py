import sqlite3

def initialize_database():
    conn = sqlite3.connect("clubbot.db")
    cursor = conn.cursor()

    # Create contacts table (if not already)
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

    # Create groups table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive'))
        );
    """)

    # Create contact_group_map table
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
