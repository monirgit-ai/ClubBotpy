import sqlite3
import csv
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QPushButton, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView,
    QAbstractItemView, QLabel, QScrollArea, QFileDialog
)
from PyQt5.QtCore import Qt
from views.add_contact_dialog import AddContactDialog
from views.profile_view import ContactProfileDialog
from views.group_manager import GroupManagerDialog


class ContactsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setup_ui()
        self.setLayout(self.layout)

    # Helper method for consistent database connection
    def db_connection(self):
        # Assumes clubbot.db is in a 'db' directory one level up from where this script is located
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, "..", "db", "clubbot.db")
        return sqlite3.connect(db_path)

    def setup_ui(self):
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by Name, WhatsApp or Club...")
        self.search_input.textChanged.connect(self.load_contacts)
        search_layout.addWidget(QLabel("Search:"))
        search_layout.addWidget(self.search_input)
        self.layout.addLayout(search_layout)

        button_layout = QHBoxLayout()
        add_btn = QPushButton("Add Contact")
        add_btn.clicked.connect(self.open_add_contact_dialog)
        import_btn = QPushButton("Import CSV")
        import_btn.clicked.connect(self.import_contacts_from_csv)
        group_btn = QPushButton("Group")
        group_btn.clicked.connect(self.open_group_manager)
        button_layout.addWidget(add_btn)
        button_layout.addWidget(import_btn)
        button_layout.addWidget(group_btn)
        self.layout.addLayout(button_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        self.contact_table = QTableWidget()
        self.contact_table.setColumnCount(6)
        self.contact_table.setHorizontalHeaderLabels(["Name", "WhatsApp", "Birthday", "Rating", "Edit", "Delete"])
        self.contact_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.contact_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.contact_table.cellClicked.connect(self.handle_cell_click)

        scroll_area.setWidget(self.contact_table)
        self.layout.addWidget(scroll_area)

        self.load_contacts()

    def open_add_contact_dialog(self):
        # When adding a new contact, contact_data is None by default
        dialog = AddContactDialog(self)
        if dialog.exec_() == dialog.Accepted:
            self.load_contacts()

    def open_group_manager(self):
        try:
            self.group_dialog = GroupManagerDialog(self)
            self.group_dialog.exec_()
            self.load_contacts()  # Refresh contacts in case group assignments changed
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def import_contacts_from_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select CSV File", "", "CSV Files (*.csv)")
        if not file_path:
            return

        conn = None
        try:
            with open(file_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)

                def normalize(row):
                    return {k.lower().replace(' ', '_').replace('.', ''): v for k, v in row.items()}

                def clean(val):
                    return val.strip() if val and val.strip().lower() != "none" else ""

                def safe_int(value):
                    try:
                        return int(float(value)) if isinstance(value, str) and '.' in value else int(value)
                    except (ValueError, TypeError):
                        return 0

                conn = self.db_connection()
                cursor = conn.cursor()
                count = 0

                # Get all column names from the contacts table dynamically
                cursor.execute("PRAGMA table_info(contacts);")
                db_column_names = [info[1] for info in cursor.fetchall()]

                # Filter out 'rowid' if present, as it's not inserted directly
                db_column_names = [col for col in db_column_names if col != 'rowid']

                for row_data in reader:
                    normalized_row = normalize(row_data)

                    # Prepare columns and values for insertion
                    columns = []
                    values = []
                    for col_name in db_column_names:
                        # Use clean for text fields, safe_int for integer fields
                        if 'int' in cursor.execute(f"PRAGMA table_info(contacts) WHERE name='{col_name}';").fetchone()[
                            2].lower():
                            values.append(safe_int(normalized_row.get(col_name, 0)))
                        else:
                            values.append(clean(normalized_row.get(col_name)))
                        columns.append(col_name)

                    # Create placeholders for the SQL query
                    placeholders = ', '.join(['?'] * len(columns))
                    columns_str = ', '.join(columns)

                    try:
                        cursor.execute(f"INSERT INTO contacts ({columns_str}) VALUES ({placeholders})", values)
                        count += 1
                    except sqlite3.IntegrityError:
                        # This typically means a UNIQUE constraint failed (e.g., duplicate whatsapp)
                        print(f"Skipping duplicate or invalid entry: {normalized_row.get('whatsapp')}")
                        continue
                    except Exception as row_error:
                        print(f"⚠️ Failed to insert row with whatsapp: {normalized_row.get('whatsapp')}: {row_error}")

                conn.commit()
                QMessageBox.information(self, "Import Complete", f"{count} contacts imported successfully.")
                self.load_contacts()

        except Exception as e:
            QMessageBox.warning(self, "Import Failed", f"An error occurred during import: {str(e)}")
        finally:
            if conn:
                conn.close()

    def load_contacts(self):
        search_term = self.search_input.text().lower().strip()
        conn = self.db_connection()
        cursor = conn.cursor()

        # We still select only basic fields for the table display to keep it readable
        cursor.execute("SELECT rowid, name, whatsapp, birthday, rating FROM contacts")
        rows = cursor.fetchall()
        conn.close()

        self.contact_table.setRowCount(0)
        for i, (rowid, name, whatsapp, birthday, rating) in enumerate(rows):
            # Filtering can now also include club names if needed, but for simplicity
            # we'll stick to name/whatsapp search here.
            # If you want to search club names, you'd need to fetch them in the query too.
            if search_term and not (search_term in (name or '').lower() or search_term in (whatsapp or '').lower()):
                continue

            row_position = self.contact_table.rowCount()
            self.contact_table.insertRow(row_position)

            name_item = QTableWidgetItem(name)
            name_item.setData(Qt.UserRole, rowid)  # Store rowid in the name item for easy retrieval
            name_item.setForeground(Qt.blue)
            name_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)  # Make name clickable

            self.contact_table.setItem(row_position, 0, name_item)
            self.contact_table.setItem(row_position, 1, QTableWidgetItem(whatsapp))
            self.contact_table.setItem(row_position, 2, QTableWidgetItem(birthday))
            self.contact_table.setItem(row_position, 3, QTableWidgetItem(str(rating) if rating is not None else ""))

            # Buttons for Edit and Delete
            edit_btn = QPushButton("Edit")
            delete_btn = QPushButton("Delete")

            # Using partial to pass rowid to clicked handlers
            # Note: lambda is used here instead of functools.partial directly for simplicity with event loop
            edit_btn.clicked.connect(lambda _, rid=rowid: self.edit_contact(rid))
            delete_btn.clicked.connect(lambda _, rid=rowid: self.delete_contact(rid))

            self.contact_table.setCellWidget(row_position, 4, edit_btn)
            self.contact_table.setCellWidget(row_position, 5, delete_btn)

    def handle_cell_click(self, row, column):
        # Only open profile when clicking on the Name column (column 0)
        if column == 0:
            item = self.contact_table.item(row, column)
            if item:
                rowid = item.data(Qt.UserRole)  # Retrieve rowid from stored data
                dialog = ContactProfileDialog(self, rowid=rowid)
                dialog.exec_()
                self.load_contacts()  # Reload contacts after profile dialog might have caused changes

    def delete_contact(self, rowid):
        confirm = QMessageBox.question(self, "Confirm Delete", "Are you sure you want to delete this contact?",
                                       QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            conn = None
            try:
                conn = self.db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM contacts WHERE rowid = ?", (rowid,))
                conn.commit()
                QMessageBox.information(self, "Success", "Contact deleted successfully.")
            except sqlite3.Error as e:
                QMessageBox.critical(self, "Database Error", f"Failed to delete contact: {str(e)}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")
            finally:
                if conn:
                    conn.close()
                self.load_contacts()  # Reload contacts to update the table

    def edit_contact(self, rowid):
        conn = None
        contact_data = {}
        try:
            conn = self.db_connection()
            cursor = conn.cursor()

            # --- CRITICAL CHANGE HERE ---
            # Get all column names from the 'contacts' table dynamically
            cursor.execute("PRAGMA table_info(contacts);")
            columns_info = cursor.fetchall()
            column_names = [col[1] for col in columns_info]

            # Fetch ALL data for the contact using SELECT *
            cursor.execute(f"SELECT * FROM contacts WHERE rowid = ?", (rowid,))
            result = cursor.fetchone()

            if result:
                # Map fetched tuple data to a dictionary using column names
                contact_data = dict(zip(column_names, result))
                contact_data["rowid"] = rowid  # Ensure rowid is also in the dictionary
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

        # Open AddContactDialog with the comprehensive contact_data
        dialog = AddContactDialog(self, contact_data)
        if dialog.exec_() == dialog.Accepted:
            self.load_contacts()  # Reload contacts to reflect changes

