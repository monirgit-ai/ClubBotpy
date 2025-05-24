import sqlite3
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QPushButton, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView,
    QAbstractItemView, QLabel, QScrollArea
)
from PyQt5.QtCore import Qt
from views.add_contact_dialog import AddContactDialog
from views.profile_view import ContactProfileDialog

class ContactsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setup_ui()
        self.setLayout(self.layout)

    def setup_ui(self):
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by Name, WhatsApp or Club...")
        self.search_input.textChanged.connect(self.load_contacts)
        search_layout.addWidget(QLabel("Search:"))
        search_layout.addWidget(self.search_input)
        self.layout.addLayout(search_layout)

        add_btn = QPushButton("Add Contact")
        add_btn.clicked.connect(self.open_add_contact_dialog)
        self.layout.addWidget(add_btn)

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
        dialog = AddContactDialog(self)
        if dialog.exec_() == dialog.Accepted:
            self.load_contacts()

    def load_contacts(self):
        search_term = self.search_input.text().lower().strip()
        conn = sqlite3.connect("clubbot.db")
        cursor = conn.cursor()
        cursor.execute("SELECT rowid, name, whatsapp, birthday, rating FROM contacts")
        rows = cursor.fetchall()
        conn.close()

        self.contact_table.setRowCount(0)
        for i, (rowid, name, whatsapp, birthday, rating) in enumerate(rows):
            if search_term and not (search_term in name.lower() or search_term in whatsapp.lower()):
                continue

            row_position = self.contact_table.rowCount()
            self.contact_table.insertRow(row_position)

            name_item = QTableWidgetItem(name)
            name_item.setData(Qt.UserRole, rowid)
            name_item.setForeground(Qt.blue)
            name_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

            self.contact_table.setItem(row_position, 0, name_item)
            self.contact_table.setItem(row_position, 1, QTableWidgetItem(whatsapp))
            self.contact_table.setItem(row_position, 2, QTableWidgetItem(birthday))
            self.contact_table.setItem(row_position, 3, QTableWidgetItem(str(rating) if rating is not None else ""))

            edit_btn = QPushButton("Edit")
            delete_btn = QPushButton("Delete")
            edit_btn.clicked.connect(lambda _, rid=rowid: self.edit_contact(rid))
            delete_btn.clicked.connect(lambda _, rid=rowid: self.delete_contact(rid))

            self.contact_table.setCellWidget(row_position, 4, edit_btn)
            self.contact_table.setCellWidget(row_position, 5, delete_btn)

    def handle_cell_click(self, row, column):
        if column == 0:  # Name column
            item = self.contact_table.item(row, column)
            if item:
                rowid = item.data(Qt.UserRole)
                dialog = ContactProfileDialog(self, rowid=rowid)
                dialog.exec_()

    def delete_contact(self, rowid):
        confirm = QMessageBox.question(self, "Confirm Delete", "Are you sure you want to delete this contact?",
                                       QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            conn = sqlite3.connect("clubbot.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM contacts WHERE rowid = ?", (rowid,))
            conn.commit()
            conn.close()
            self.load_contacts()

    def edit_contact(self, rowid):
        conn = sqlite3.connect("clubbot.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name, whatsapp, birthday, instagram, rating, last_club, visit_date, category, recent_visit, club_visits FROM contacts WHERE rowid = ?", (rowid,))
        result = cursor.fetchone()
        if result:
            contact_data = dict(zip([
                "name", "whatsapp", "birthday", "instagram", "rating", "last_club",
                "visit_date", "category", "recent_visit", "club_visits"
            ], result))
            contact_data["rowid"] = rowid
            dialog = AddContactDialog(self, contact_data)
            if dialog.exec_() == dialog.Accepted:
                self.load_contacts()
        conn.close()
