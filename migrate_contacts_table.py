import sqlite3

conn = sqlite3.connect("clubbot.db")
cursor = conn.cursor()

commands = [
    "ALTER TABLE contacts ADD COLUMN instagram TEXT",
    "ALTER TABLE contacts ADD COLUMN rating INTEGER",
    "ALTER TABLE contacts ADD COLUMN last_club TEXT",
    "ALTER TABLE contacts ADD COLUMN visit_date TEXT",
    "ALTER TABLE contacts ADD COLUMN category TEXT",
    "ALTER TABLE contacts ADD COLUMN recent_visit TEXT",
    "ALTER TABLE contacts ADD COLUMN club_visits INTEGER",
    "ALTER TABLE contacts ADD COLUMN mon INTEGER DEFAULT 0",
    "ALTER TABLE contacts ADD COLUMN tue INTEGER DEFAULT 0",
    "ALTER TABLE contacts ADD COLUMN wed INTEGER DEFAULT 0",
    "ALTER TABLE contacts ADD COLUMN thu INTEGER DEFAULT 0",
    "ALTER TABLE contacts ADD COLUMN fri INTEGER DEFAULT 0",
    "ALTER TABLE contacts ADD COLUMN sat INTEGER DEFAULT 0",
    "ALTER TABLE contacts ADD COLUMN sun INTEGER DEFAULT 0",
    "ALTER TABLE contacts ADD COLUMN lio INTEGER DEFAULT 0",
    "ALTER TABLE contacts ADD COLUMN tabu INTEGER DEFAULT 0",
    "ALTER TABLE contacts ADD COLUMN dear_d INTEGER DEFAULT 0",
    "ALTER TABLE contacts ADD COLUMN reign INTEGER DEFAULT 0",
    "ALTER TABLE contacts ADD COLUMN tape INTEGER DEFAULT 0",
    "ALTER TABLE contacts ADD COLUMN maddox INTEGER DEFAULT 0",
    "ALTER TABLE contacts ADD COLUMN dolce INTEGER DEFAULT 0",
    "ALTER TABLE contacts ADD COLUMN gallery INTEGER DEFAULT 0",
    "ALTER TABLE contacts ADD COLUMN rex_rooms INTEGER DEFAULT 0",
    "ALTER TABLE contacts ADD COLUMN selene INTEGER DEFAULT 0"
]

for cmd in commands:
    try:
        cursor.execute(cmd)
    except sqlite3.OperationalError as e:
        print(f"Skipped: {cmd} — {e}")

conn.commit()
conn.close()
print("Migration complete.")
