import sqlite3
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QPushButton, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QMessageBox
)

class ContactsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setup_ui()
        self.setLayout(self.layout)

    def setup_ui(self):
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Full Name")
        self.whatsapp_input = QLineEdit()
        self.whatsapp_input.setPlaceholderText("WhatsApp Number")
        self.birthday_input = QLineEdit()
        self.birthday_input.setPlaceholderText("Birthday (YYYY-MM-DD)")

        form_layout = QHBoxLayout()
        form_layout.addWidget(self.name_input)
        form_layout.addWidget(self.whatsapp_input)
        form_layout.addWidget(self.birthday_input)

        add_btn = QPushButton("Add Contact")
        add_btn.clicked.connect(self.add_contact)

        self.layout.addLayout(form_layout)
        self.layout.addWidget(add_btn)

        self.contact_table = QTableWidget()
        self.contact_table.setColumnCount(3)
        self.contact_table.setHorizontalHeaderLabels(["Name", "WhatsApp", "Birthday"])
        self.layout.addWidget(self.contact_table)

        self.load_contacts()

    def add_contact(self):
        name = self.name_input.text()
        whatsapp = self.whatsapp_input.text()
        birthday = self.birthday_input.text()

        if not name or not whatsapp:
            QMessageBox.warning(self, "Input Error", "Name and WhatsApp are required.")
            return

        conn = sqlite3.connect("clubbot.db")
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO contacts (name, whatsapp, birthday) VALUES (?, ?, ?)",
                           (name, whatsapp, birthday))
            conn.commit()
            self.load_contacts()
            self.name_input.clear()
            self.whatsapp_input.clear()
            self.birthday_input.clear()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Duplicate Entry", "This WhatsApp number already exists.")
        finally:
            conn.close()

    def load_contacts(self):
        conn = sqlite3.connect("clubbot.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name, whatsapp, birthday FROM contacts")
        rows = cursor.fetchall()
        conn.close()

        self.contact_table.setRowCount(len(rows))
        for i, (name, whatsapp, birthday) in enumerate(rows):
            self.contact_table.setItem(i, 0, QTableWidgetItem(name))
            self.contact_table.setItem(i, 1, QTableWidgetItem(whatsapp))
            self.contact_table.setItem(i, 2, QTableWidgetItem(birthday))
