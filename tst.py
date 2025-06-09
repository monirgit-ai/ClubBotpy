import sqlite3

conn = sqlite3.connect("clubbot.db")  # adjust path if needed
cursor = conn.cursor()

cursor.execute("DELETE FROM messages;")
conn.commit()
conn.close()

print("✅ All contacts deleted.")
