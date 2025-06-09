import sqlite3
import hashlib
import os
import sys

# Assume db/clubbot.db relative to this script for simplicity,
# if this script is in the root ClubBotPy directory.
# Adjust db_path if this script is placed elsewhere.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "db", "clubbot.db")

def hash_password(password):
    """Hashes a password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()

def create_admin_user(username, password):
    """Creates an admin user in the database."""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Check if the users table exists (it should after init_db_schema.py runs)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
        if not cursor.fetchone():
            print(f"Error: 'users' table not found in {DB_PATH}.")
            print("Please ensure the database schema is initialized by running 'python main.py' first.")
            return False

        hashed_password = hash_password(password)

        # Check if username already exists
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            print(f"User '{username}' already exists. Please choose a different username.")
            return False

        cursor.execute("INSERT INTO users (username, password_hash, role, status) VALUES (?, ?, 'admin', 'active')",
                       (username, hashed_password))
        conn.commit()
        print(f"✅ Admin user '{username}' created successfully!")
        return True
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("--- ClubBot Admin User Creation ---")
    print(f"Database path: {DB_PATH}")

    if not os.path.exists(DB_PATH):
        print("\nDatabase file not found.")
        print("Please ensure the database is initialized by running 'python main.py' at least once,")
        print(f"and that '{os.path.basename(DB_PATH)}' exists at '{os.path.dirname(DB_PATH)}'.")
        sys.exit(1)

    admin_username = input("Enter desired admin username: ").strip()
    admin_password = input("Enter desired admin password: ").strip()

    if not admin_username or not admin_password:
        print("Username and password cannot be empty.")
    else:
        create_admin_user(admin_username, admin_password)

