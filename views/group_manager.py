import sqlite3
import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QMessageBox, QComboBox, QCheckBox
)
from PyQt5.QtCore import Qt

class GroupManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Group Manager")
        self.setMinimumSize(800, 500)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.group_name_input = QLineEdit()
        self.group_name_input.setPlaceholderText("Enter Group Name")
        self.create_group_btn = QPushButton("Create Group")
        self.create_group_btn.clicked.connect(self.create_group)

        self.group_select = QComboBox()
        self.group_select.currentIndexChanged.connect(self.load_group_contacts)
        self.status_toggle_btn = QPushButton("Toggle Active/Inactive")
        self.status_toggle_btn.clicked.connect(self.toggle_group_status)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search contacts by name or WhatsApp")
        self.search_input.textChanged.connect(self.load_contacts)

        self.rating_filter = QComboBox()
        self.rating_filter.addItem("All Ratings")
        self.rating_filter.addItems([str(i) for i in range(1, 6)])
        self.rating_filter.currentIndexChanged.connect(self.load_contacts)

        top_layout = QHBoxLayout()
        top_layout.addWidget(self.group_name_input)
        top_layout.addWidget(self.create_group_btn)
        top_layout.addWidget(self.group_select)
        top_layout.addWidget(self.status_toggle_btn)
        self.layout.addLayout(top_layout)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(self.search_input)
        filter_layout.addWidget(QLabel("Rating:"))
        filter_layout.addWidget(self.rating_filter)
        self.layout.addLayout(filter_layout)

        self.contacts_table = QTableWidget()
        self.contacts_table.setColumnCount(4)
        self.contacts_table.setHorizontalHeaderLabels(["Name", "WhatsApp", "Rating", "Add to Group"])
        self.layout.addWidget(self.contacts_table)

        self.load_groups()
        self.load_contacts()

    def create_group(self):
        name = self.group_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Input Error", "Group name cannot be empty.")
            return
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), "../db/clubbot.db"))
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO groups (name) VALUES (?)", (name,))
            conn.commit()
            self.group_name_input.clear()
            self.load_groups()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Duplicate", "Group with this name already exists.")
        finally:
            conn.close()

    def load_groups(self):
        self.group_select.clear()
        conn = sqlite3.connect("db/clubbot.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, status FROM groups")
        self.groups = cursor.fetchall()
        for group in self.groups:
            self.group_select.addItem(f"{group[1]} ({group[2]})", group[0])
        conn.close()

    def toggle_group_status(self):
        index = self.group_select.currentIndex()
        if index < 0:
            return
        group_id = self.group_select.itemData(index)
        current_status = self.groups[index][2]
        new_status = "inactive" if current_status == "active" else "active"
        conn = sqlite3.connect("db/clubbot.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE groups SET status = ? WHERE id = ?", (new_status, group_id))
        conn.commit()
        conn.close()
        self.load_groups()

    def load_contacts(self):
        search = self.search_input.text().lower()
        rating_filter = self.rating_filter.currentText()

        conn = sqlite3.connect("db/clubbot.db")
        cursor = conn.cursor()
        query = "SELECT rowid, name, whatsapp, rating FROM contacts"
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()

        filtered = []
        for r in rows:
            if search and search not in r[1].lower() and search not in r[2]:
                continue
            if rating_filter != "All Ratings" and str(r[3]) != rating_filter:
                continue
            filtered.append(r)

        self.contacts_table.setRowCount(0)
        for i, (cid, name, whatsapp, rating) in enumerate(filtered):
            self.contacts_table.insertRow(i)
            self.contacts_table.setItem(i, 0, QTableWidgetItem(name))
            self.contacts_table.setItem(i, 1, QTableWidgetItem(whatsapp))
            self.contacts_table.setItem(i, 2, QTableWidgetItem(str(rating)))

            checkbox = QCheckBox()
            checkbox.stateChanged.connect(lambda _, c=cid: self.add_or_remove_contact(c))
            self.contacts_table.setCellWidget(i, 3, checkbox)

    def add_or_remove_contact(self, contact_id):
        index = self.group_select.currentIndex()
        if index < 0:
            return
        group_id = self.group_select.itemData(index)
        conn = sqlite3.connect("db/clubbot.db")
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT OR IGNORE INTO contact_group_map (contact_id, group_id) VALUES (?, ?)", (contact_id, group_id))
            conn.commit()
        finally:
            conn.close()

    def load_group_contacts(self):
        self.load_contacts()

    def open_group_manager(self):
        from views.group_manager import GroupManagerDialog
        dialog = GroupManagerDialog(self)
        dialog.exec_()
