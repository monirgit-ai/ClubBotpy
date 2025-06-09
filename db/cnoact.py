import sqlite3
import os
import hashlib # For password hashing

def initialize_database():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, "clubbot.db")

    os.makedirs(base_dir, exist_ok=True) # Ensure the 'db' folder exists

    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # --- USERS TABLE ---
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('admin', 'user')),
                status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive'))
            );
        """)

        # Define all base column definitions for the contacts table
        contact_columns = [
            "name TEXT",
            "whatsapp TEXT UNIQUE",
            "birthday TEXT",
            "instagram TEXT",
            "rating INTEGER",
            "last_club TEXT",
            "visit_date TEXT",
            "category TEXT",
            "recent_visit TEXT",
            "club_visits INTEGER"
        ]

        # Define week days and club names to generate frequency columns
        week_days = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
        club_names_for_schema = [
            "Cirque Le Soir", "Madox", "Tabu", "Leo", "Reign", "Tape",
            "Dear Darling", "The Box", "Lio", "Dolce", "Gallery", "Rex Rooms", "Selene"
        ]

        # Generate club visit frequency columns dynamically
        for club_name in club_names_for_schema:
            club_key = club_name.lower().replace(' ', '_').replace('.', '')
            if club_name == "Dear Darling":
                club_key = "dear_d" # Ensure consistency with the key used in add_contact_dialog.py

            for day in week_days:
                column_name = f"{club_key}_{day}"
                contact_columns.append(f"{column_name} INTEGER DEFAULT 0")

        # Join all column definitions for the CREATE TABLE statement
        columns_definition_sql = ", ".join(contact_columns)

        # Create contacts table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS contacts (
                {columns_definition_sql}
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

        # Groups table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive'))
            );
        """)

        # Contact-Group map table
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

        # Delivery Report table (added from sendswhatsapp.py's logging)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS delivery_report (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                whatsapp TEXT NOT NULL,
                status TEXT NOT NULL,
                logged_at TEXT NOT NULL
            );
        """)

        # Contact Message Log table (from campaign_view.py)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contact_message_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                sent_at TEXT NOT NULL,
                FOREIGN KEY (contact_id) REFERENCES contacts(rowid),
                FOREIGN KEY (message_id) REFERENCES messages(id),
                UNIQUE(contact_id, message_id) -- Ensures a specific message is logged once per contact
            );
        """)

        conn.commit()
        print("✅ Database schema initialized/updated.")

    except sqlite3.Error as e:
        print(f"❌ Database error during initialization: {e}")
    except Exception as e:
        print(f"❌ An unexpected error occurred during database initialization: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    initialize_database()
