import sqlite3
import hashlib
import os
import requests  # For HTTP requests to Google Apps Script
import uuid  # For getting MAC address
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox,
    QHBoxLayout, QGroupBox, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt

# --- Google Sheets Access Control Configuration ---
# REPLACE THIS WITH YOUR DEPLOYED GOOGLE APPS SCRIPT WEB APP URL
# Example: "https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID/exec"
GOOGLE_APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzlZsY44p-P7BQyTkgOEg_Yd9Oly5t5SHTihOMIdFT6WM7CxnKTs6dipqLzI2bPlZTL/exec"  # <--- UPDATED!


def get_mac_address():
    """Retrieves the MAC address of the current machine."""
    # Using uuid.getnode() which is cross-platform.
    # Format it as XX:XX:XX:XX:XX:XX
    mac_num = uuid.getnode()
    mac_hex = ':'.join(f"{(mac_num >> i) & 0xff:02x}" for i in range(40, -1, -8))
    return mac_hex


class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ClubBot Login")
        self.setFixedSize(400, 250)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        main_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        login_group_box = QGroupBox("Login")
        login_form_layout = QVBoxLayout()
        login_group_box.setLayout(login_form_layout)

        username_label = QLabel("Username:")
        username_label.setAlignment(Qt.AlignLeft)
        login_form_layout.addWidget(username_label)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.setFixedHeight(30)
        self.username_input.setStyleSheet("padding: 5px; border-radius: 5px; border: 1px solid #ccc;")
        login_form_layout.addWidget(self.username_input)

        password_label = QLabel("Password:")
        password_label.setAlignment(Qt.AlignLeft)
        login_form_layout.addWidget(password_label)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setFixedHeight(30)
        self.password_input.setStyleSheet("padding: 5px; border-radius: 5px; border: 1px solid #ccc;")
        login_form_layout.addWidget(self.password_input)

        login_form_layout.addSpacing(15)

        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.handle_login)  # Typo 'q' removed here
        self.login_button.setFixedHeight(35)
        self.login_button.setStyleSheet(
            "QPushButton {"
            "   background-color: #4CAF50; color: white; border-radius: 8px;"
            "   font-weight: bold;"
            "}"
            "QPushButton:hover { background-color: #45a049; }"
            "QPushButton:pressed { background-color: #367c39; }"
        )
        login_form_layout.addWidget(self.login_button)

        self.message_label = QLabel("")
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setStyleSheet("color: red; font-weight: bold;")
        login_form_layout.addWidget(self.message_label)

        main_layout.addWidget(login_group_box)

        main_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        self.logged_in_user_id = None
        self.logged_in_username = None
        self.logged_in_role = None

    def db_connection(self):
        """Helper method to establish local database connection."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, "..", "db", "clubbot.db")
        return sqlite3.connect(db_path)

    def hash_password(self, password):
        """Hashes a password using SHA256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def authenticate_user(self, username, password):
        """
        Authenticates a user against the local database.
        Returns (user_id, username, role) tuple on success, None otherwise.
        """
        conn = None
        try:
            conn = self.db_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT id, username, password_hash, role, status FROM users WHERE username = ?",
                           (username,))
            user_record = cursor.fetchone()

            if user_record:
                user_id, db_username, stored_password_hash, role, status = user_record
                if status == 'inactive':
                    self.message_label.setText("Account is inactive. Please contact admin.")
                    return None

                entered_password_hash = self.hash_password(password)
                if entered_password_hash == stored_password_hash:
                    return user_id, db_username, role
                else:
                    self.message_label.setText("Invalid username or password.")
            else:
                self.message_label.setText("Invalid username or password.")
            return None
        except sqlite3.Error as e:
            self.message_label.setText(f"Local DB error: {e}")
            print(f"Login local DB error: {e}")
            return None
        except Exception as e:
            self.message_label.setText(f"An unexpected error occurred during local DB authentication: {e}")
            print(f"Login unexpected error during local DB auth: {e}")
            return None
        finally:
            if conn:
                conn.close()

    def _check_remote_access_and_log(self, username, mac_address):
        """
        Communicates with the Google Apps Script to check access status
        and log the login attempt.
        """
        if not GOOGLE_APPS_SCRIPT_URL or GOOGLE_APPS_SCRIPT_URL == "YOUR_GOOGLE_APPS_SCRIPT_WEB_APP_URL_HERE":
            self.message_label.setText("Google Apps Script URL not configured. Access check skipped.")
            print("WARNING: GOOGLE_APPS_SCRIPT_URL is not set. Remote access control is disabled.")
            return True  # Allow access if URL is not configured

        try:
            # First, check the access status for this MAC address.
            # The GAS script will return 'allowed' or 'denied', and also log/update
            # the entry if it's a new MAC or an existing 'allowed' one.
            params = {"action": "check", "mac": mac_address, "username": username}
            response = requests.get(GOOGLE_APPS_SCRIPT_URL, params=params, timeout=10)
            response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)

            result = response.text.strip().lower()
            print(f"GAS response for MAC check ({mac_address}): {result}")

            if result == "allowed":
                return True
            elif result == "denied":
                self.message_label.setText("Configuration error Code:Access. Please contact developer.")
                QMessageBox.warning(self, "Access Denied",
                                    "Configuration error Code:Access. Please contact the developer.")
                return False
            else:
                self.message_label.setText(f"Unknown response from access server: {result}")
                QMessageBox.critical(self, "Access Error",
                                     "Unknown response from access control server. Please contact developer.")
                return False
        except requests.exceptions.Timeout:
            self.message_label.setText("Access timed out. Please check your network.")
            QMessageBox.critical(self, "Network Error", "Connection to access timed out. Please try again.")
            return False
        except requests.exceptions.RequestException as e:
            self.message_label.setText(f"Error connecting to access server: {e}")
            QMessageBox.critical(self, "Network Error",
                                 f"Could not reach access control . Please check your network/URL. Error: {e}")
            return False
        except Exception as e:
            self.message_label.setText(f"An unexpected error occurred during  access check: {e}")
            print(f"Unexpected error in access check: {e}")
            return False

    def handle_login(self):
        """Handles the login button click event."""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        self.message_label.clear()  # Clear previous messages

        if not username or not password:
            self.message_label.setText("Please enter both username and password.")
            return

        current_mac_address = get_mac_address()
        if not current_mac_address:
            self.message_label.setText("Could not retrieve MAC address. Cannot verify access.")
            QMessageBox.critical(self, "MAC Error",
                                 "Unable to retrieve MAC address. Please check your network connection.")
            return

        # 1. Check MAC access from Google Sheet AND log/update the entry
        # The GAS script handles logging/updating based on the 'check' action
        # If the MAC is 'deny' in sheet, it will return False and show an alert.
        if not self._check_remote_access_and_log(username, current_mac_address):
            return  # Access denied, so stop login process

        # 2. Authenticate user against local database (only if remote access is allowed)
        user_info = self.authenticate_user(username, password)

        if user_info:
            self.logged_in_user_id = user_info[0]
            self.logged_in_username = user_info[1]
            self.logged_in_role = user_info[2]

            self.accept()  # Close dialog and signal success
        else:
            # Message is already set by authenticate_user method for local DB auth issues
            pass
