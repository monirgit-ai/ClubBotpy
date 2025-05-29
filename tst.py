import sqlite3

conn = sqlite3.connect("db/clubbot.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS delivery_report (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    whatsapp TEXT NOT NULL,
    status TEXT NOT NULL,
    logged_at TEXT DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()
conn.close()

print("✅ delivery_report table created successfully.")
