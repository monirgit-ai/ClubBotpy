import os
import sqlite3
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QHBoxLayout, QMessageBox, QCheckBox
)
from PyQt5.QtCore import Qt

class ContactsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.db_path = os.path.join(os.path.dirname(__file__), "../db/clubbot.db")
        self.setup_ui()
        self.load_contacts()

    def setup_ui(self):
        layout = QVBoxLayout()

        # --- Add Contact Form ---
        form_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Full Name")
        self.whatsapp_input = QLineEdit()
        self.whatsapp_input.setPlaceholderText("WhatsApp Number")
        self.instagram_input = QLineEdit()
        self.instagram_input.setPlaceholderText("Instagram ID")
        self.rating_input = QLineEdit()
        self.rating_input.setPlaceholderText("Rating (1-10)")

        add_button = QPushButton("➕ Add Contact")
        add_button.clicked.connect(self.add_contact)

        form_layout.addWidget(self.name_input)
        form_layout.addWidget(self.whatsapp_input)
        form_layout.addWidget(self.instagram_input)
        form_layout.addWidget(self.rating_input)
        form_layout.addWidget(add_button)
        layout.addLayout(form_layout)

        # --- Table of Contacts ---
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Select", "Name", "WhatsApp", "Instagram", "Rating"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        # --- Buttons ---
        button_layout = QHBoxLayout()
        self.select_all_checkbox = QCheckBox("Select All")
        self.select_all_checkbox.stateChanged.connect(self.toggle_all_checkboxes)
        delete_button = QPushButton("🗑️ Delete Selected")
        delete_button.clicked.connect(self.delete_selected_contacts)

        button_layout.addWidget(self.select_all_checkbox)
        button_layout.addStretch()
        button_layout.addWidget(delete_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def db_connection(self):
        return sqlite3.connect(self.db_path)

    def load_contacts(self):
        self.table.setRowCount(0)
        conn = self.db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT rowid, name, whatsapp, instagram, rating FROM contacts")
        rows = cursor.fetchall()
        conn.close()

        for i, row in enumerate(rows):
            self.table.insertRow(i)

            checkbox = QCheckBox()
            self.table.setCellWidget(i, 0, checkbox)

            for j in range(1, 5):
                item = QTableWidgetItem(str(row[j]))
                item.setData(Qt.UserRole, row[0])  # store contact ID
                self.table.setItem(i, j, item)

    def toggle_all_checkboxes(self, state):
        for i in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(i, 0)
            if checkbox:
                checkbox.setChecked(state == Qt.Checked)

    def add_contact(self):
        name = self.name_input.text().strip()
        whatsapp = self.whatsapp_input.text().strip()
        instagram = self.instagram_input.text().strip()
        rating = self.rating_input.text().strip()

        if not name or not whatsapp:
            QMessageBox.warning(self, "Missing Info", "Name and WhatsApp are required.")
            return

        try:
            conn = self.db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO contacts (name, whatsapp, instagram, rating)
                VALUES (?, ?, ?, ?)
            """, (name, whatsapp, instagram, rating))
            conn.commit()
            conn.close()

            self.name_input.clear()
            self.whatsapp_input.clear()
            self.instagram_input.clear()
            self.rating_input.clear()

            self.load_contacts()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add contact: {str(e)}")

    def delete_selected_contacts(self):
        selected_ids = []
        for i in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(i, 0)
            if checkbox and checkbox.isChecked():
                item = self.table.item(i, 1)  # any column with contact ID
                if item:
                    contact_id = item.data(Qt.UserRole)
                    selected_ids.append(contact_id)

        if not selected_ids:
            QMessageBox.information(self, "No Selection", "Please select contacts to delete.")
            return

        confirm = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete {len(selected_ids)} contact(s)?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return

        try:
            conn = self.db_connection()
            cursor = conn.cursor()
            cursor.executemany("DELETE FROM contacts WHERE rowid = ?", [(i,) for i in selected_ids])
            conn.commit()
            conn.close()
            self.load_contacts()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete contacts: {str(e)}")
