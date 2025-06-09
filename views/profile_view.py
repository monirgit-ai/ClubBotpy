import sqlite3
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QGridLayout, QPushButton, QHBoxLayout, QMessageBox, QWidget
)
from PyQt5.QtCore import Qt  # Import Qt for alignment
from views.add_contact_dialog import AddContactDialog
import os


class ContactProfileDialog(QDialog):
    def __init__(self, parent=None, rowid=None):
        super().__init__(parent)
        self.setWindowTitle("Contact Profile")
        self.setMinimumWidth(600)  # Increased width for the new table
        self.rowid = rowid
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Basic contact info display
        self.info_labels = {}
        self.grid = QGridLayout()
        self.layout.addLayout(self.grid)
        self.build_ui()  # Builds the initial contact info grid

        # Add a separator for better visual organization
        self.layout.addWidget(QLabel("---"))

        # Club Visit Frequency display
        self.layout.addWidget(QLabel("<b>Club Visit Frequency:</b>"))  # Bold title
        self.club_visit_display_grid = QGridLayout()
        self.layout.addLayout(self.club_visit_display_grid)
        self.build_club_visit_frequency_ui()  # Builds the club visit frequency grid

        self.load_contact()  # Load all data after UI is built

        # Buttons layout at the bottom
        btn_layout = QHBoxLayout()
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.clicked.connect(self.open_edit_dialog)
        btn_layout.addWidget(self.edit_btn)
        self.layout.addLayout(btn_layout)

    # Helper method for consistent database connection
    def db_connection(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, "..", "db", "clubbot.db")
        return sqlite3.connect(db_path)

    def build_ui(self):
        """Builds the UI for basic contact information."""
        fields = [
            "Name", "WhatsApp", "Instagram", "Birthday", "Rating",
            "Last Club", "Visit Date", "Category", "Recent Visit", "Club Visits"
        ]
        self.field_keys = [
            "name", "whatsapp", "instagram", "birthday", "rating",
            "last_club", "visit_date", "category", "recent_visit", "club_visits"
        ]
        for i, label_text in enumerate(fields):
            self.grid.addWidget(QLabel(f"<b>{label_text}:</b>", self), i, 0)  # Bold field labels
            self.info_labels[label_text] = QLabel("-", self)
            self.grid.addWidget(self.info_labels[label_text], i, 1)

    def build_club_visit_frequency_ui(self):
        """Builds the read-only UI for club visit frequency."""
        self.week_days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        self.club_names = [
            "Cirque Le Soir", "Madox", "Tabu", "Leo", "Reign", "Tape",
            "Dear Darling", "The Box", "Lio", "Dolce", "Gallery", "Rex Rooms", "Selene"
        ]
        self.club_names.sort()  # Ensure consistent order

        # Add day headers to the grid (first row, starting from column 1)
        for col, day in enumerate(self.week_days):
            day_label = QLabel(day)
            day_label.setAlignment(Qt.AlignCenter)
            self.club_visit_display_grid.addWidget(day_label, 0, col + 1)

        self.club_day_display_labels = {}  # Store QLabel references for updating
        for row, club in enumerate(self.club_names):
            # Generate club_key consistent with add_contact_dialog.py and init_db_schema.py
            club_key = club.lower().replace(' ', '_').replace('.', '')

            self.club_day_display_labels[club_key] = {}

            club_label = QLabel(club)
            self.club_visit_display_grid.addWidget(club_label, row + 1, 0)  # +1 for header row

            for col, day in enumerate(self.week_days):
                day_key = day.lower()

                # Create a QLabel to display the value
                value_label = QLabel("0")  # Default to 0
                value_label.setAlignment(Qt.AlignCenter)
                self.club_day_display_labels[club_key][day_key] = value_label
                self.club_visit_display_grid.addWidget(value_label, row + 1, col + 1)

    def load_contact(self):
        """Loads contact data from DB and populates all UI elements."""
        conn = None
        full_contact_data = {}
        try:
            conn = self.db_connection()
            cursor = conn.cursor()

            # Get all column names from the 'contacts' table dynamically
            cursor.execute("PRAGMA table_info(contacts);")
            columns_info = cursor.fetchall()
            column_names = [col[1] for col in columns_info]

            # Fetch all data for the contact using SELECT *
            cursor.execute(f"SELECT * FROM contacts WHERE rowid = ?", (self.rowid,))
            result = cursor.fetchone()

            if result:
                # Map fetched tuple data to a dictionary using column names
                full_contact_data = dict(zip(column_names, result))

                # Populate basic info labels
                for key in self.field_keys:
                    label = next((f for f, k in zip(self.info_labels.keys(), self.field_keys) if k == key), None)
                    if label and key in full_contact_data:
                        self.info_labels[label].setText(
                            str(full_contact_data[key]) if full_contact_data[key] is not None else "-")

                # Populate club visit frequency labels
                for club_key, day_labels in self.club_day_display_labels.items():
                    for day_key, label_widget in day_labels.items():
                        column_name = f"{club_key}_{day_key}"
                        if column_name in full_contact_data and full_contact_data[column_name] is not None:
                            label_widget.setText(str(full_contact_data[column_name]))
                        else:
                            label_widget.setText("0")  # Default if column is missing or value is None
            else:
                QMessageBox.warning(self, "Error", "Contact not found.")

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load contact: {str(e)}")
        except Exception as ex:
            QMessageBox.critical(self, "Unexpected Error", f"An unexpected error occurred: {str(ex)}")
        finally:
            if conn:
                conn.close()

    def open_edit_dialog(self):
        """Opens the AddContactDialog for editing, passing all contact data."""
        conn = None
        contact_data = {}
        try:
            conn = self.db_connection()
            cursor = conn.cursor()

            # Get all column names from the 'contacts' table dynamically
            cursor.execute("PRAGMA table_info(contacts);")
            columns_info = cursor.fetchall()
            column_names = [col[1] for col in columns_info]

            # Fetch all data for the contact using SELECT *
            cursor.execute(f"SELECT * FROM contacts WHERE rowid = ?", (self.rowid,))
            result = cursor.fetchone()

            if result:
                contact_data = dict(zip(column_names, result))
                contact_data["rowid"] = self.rowid  # Add rowid to the dictionary
            else:
                QMessageBox.warning(self, "Error", "Contact data not found for editing.")
                return

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"Failed to retrieve contact data for editing: {str(e)}")
            return
        except Exception as ex:
            QMessageBox.critical(self, "Unexpected Error", f"An unexpected error occurred: {str(ex)}")
            return
        finally:
            if conn:
                conn.close()

        # Pass the full contact_data dictionary to AddContactDialog
        dialog = AddContactDialog(self, contact_data)
        if dialog.exec_() == dialog.Accepted:
            self.load_contact()  # Reload contact profile to reflect changes
