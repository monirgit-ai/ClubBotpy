import sqlite3
import hashlib
import os
from functools import partial
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox, QComboBox, QHeaderView,
    QInputDialog
)
from PyQt5.QtCore import Qt


class UserManagementTab(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.setup_ui()
        self.load_users()

    def db_connection(self):
        """Helper method to establish database connection."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # Assumes clubbot.db is in 'db' folder, one level up from 'views'
        db_path = os.path.join(base_dir, "..", "db", "clubbot.db")
        return sqlite3.connect(db_path)

    def hash_password(self, password):
        """Hashes a password using SHA256 (consistent with create_admin.py and login_dialog.py)."""
        return hashlib.sha256(password.encode()).hexdigest()

    def setup_ui(self):
        # Add New User Section
        add_user_layout = QHBoxLayout()
        self.new_username_input = QLineEdit()
        self.new_username_input.setPlaceholderText("New Username")
        self.new_password_input = QLineEdit()
        self.new_password_input.setPlaceholderText("New Password")
        self.new_password_input.setEchoMode(QLineEdit.Password)
        self.new_role_combo = QComboBox()
        self.new_role_combo.addItems(["user", "admin"])  # Default to 'user' for new accounts
        add_user_btn = QPushButton("Add New User")
        add_user_btn.clicked.connect(self.add_user)

        add_user_layout.addWidget(self.new_username_input)
        add_user_layout.addWidget(self.new_password_input)
        add_user_layout.addWidget(self.new_role_combo)
        add_user_layout.addWidget(add_user_btn)
        self.layout.addLayout(add_user_layout)

        self.layout.addWidget(QLabel("<b>Existing Users:</b>"))

        # Users Table
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(5)  # Username, Role, Status, Change Password, Toggle Status
        self.user_table.setHorizontalHeaderLabels(["Username", "Role", "Status", "Change Password", "Actions"])
        self.user_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.user_table.setEditTriggers(QTableWidget.NoEditTriggers)  # Make table read-only

        self.layout.addWidget(self.user_table)

    def load_users(self):
        """Loads all users from the database into the table."""
        conn = None
        try:
            conn = self.db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, username, role, status FROM users ORDER BY username ASC")
            users = cursor.fetchall()
            conn.close()

            self.user_table.setRowCount(0)  # Clear existing rows
            for row_idx, (user_id, username, role, status) in enumerate(users):
                self.user_table.insertRow(row_idx)
                self.user_table.setItem(row_idx, 0, QTableWidgetItem(username))
                self.user_table.setItem(row_idx, 1, QTableWidgetItem(role))
                self.user_table.setItem(row_idx, 2, QTableWidgetItem(status))

                # Change Password Button
                change_pass_btn = QPushButton("Change Password")
                change_pass_btn.clicked.connect(partial(self.change_user_password, user_id))
                self.user_table.setCellWidget(row_idx, 3, change_pass_btn)

                # Action Buttons (Toggle Status, Delete)
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins for compact buttons

                toggle_status_btn = QPushButton("Deactivate" if status == 'active' else "Activate")
                toggle_status_btn.clicked.connect(partial(self.toggle_user_status, user_id, status))
                actions_layout.addWidget(toggle_status_btn)

                delete_btn = QPushButton("Delete")
                delete_btn.clicked.connect(partial(self.delete_user, user_id, username))
                actions_layout.addWidget(delete_btn)

                self.user_table.setCellWidget(row_idx, 4, actions_widget)

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load users: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")
        finally:
            if conn:
                conn.close()

    def add_user(self):
        """Adds a new user to the database."""
        username = self.new_username_input.text().strip()
        password = self.new_password_input.text().strip()
        role = self.new_role_combo.currentText()

        if not username or not password:
            QMessageBox.warning(self, "Input Error", "Username and password cannot be empty.")
            return

        conn = None
        try:
            conn = self.db_connection()
            cursor = conn.cursor()
            hashed_password = self.hash_password(password)

            cursor.execute("INSERT INTO users (username, password_hash, role, status) VALUES (?, ?, ?, 'active')",
                           (username, hashed_password, role))
            conn.commit()
            QMessageBox.information(self, "Success", f"User '{username}' added successfully!")
            self.new_username_input.clear()
            self.new_password_input.clear()
            self.load_users()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Duplicate User",
                                f"User '{username}' already exists. Please choose a different username.")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to add user: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")
        finally:
            if conn:
                conn.close()

    def change_user_password(self, user_id):
        """Allows changing the password for a selected user."""
        new_password, ok = QInputDialog.getText(self, "Change Password", "Enter new password:", QLineEdit.Password)
        if ok and new_password:
            conn = None
            try:
                conn = self.db_connection()
                cursor = conn.cursor()
                hashed_password = self.hash_password(new_password)
                cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hashed_password, user_id))
                conn.commit()
                QMessageBox.information(self, "Success", "Password changed successfully!")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Database Error", f"Failed to change password: {str(e)}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")
            finally:
                if conn:
                    conn.close()
        elif ok and not new_password:
            QMessageBox.warning(self, "Input Error", "Password cannot be empty.")

    def toggle_user_status(self, user_id, current_status):
        """Toggles a user's active/inactive status."""
        new_status = 'inactive' if current_status == 'active' else 'active'
        confirm = QMessageBox.question(self, "Confirm Status Change",
                                       f"Are you sure you want to set this user to '{new_status}'?",
                                       QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            conn = None
            try:
                conn = self.db_connection()
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET status = ? WHERE id = ?", (new_status, user_id))
                conn.commit()
                QMessageBox.information(self, "Success", f"User status changed to '{new_status}'.")
                self.load_users()  # Refresh table
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Database Error", f"Failed to change user status: {str(e)}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")
            finally:
                if conn:
                    conn.close()

    def delete_user(self, user_id, username):
        """Deletes a user from the database."""
        confirm = QMessageBox.question(self, "Confirm Delete",
                                       f"Are you sure you want to delete user '{username}'?",
                                       QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            conn = None
            try:
                conn = self.db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
                conn.commit()
                QMessageBox.information(self, "Success", f"User '{username}' deleted successfully.")
                self.load_users()  # Refresh table
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Database Error", f"Failed to delete user: {str(e)}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")
            finally:
                if conn:
                    conn.close()
