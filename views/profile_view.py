import sqlite3
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QGridLayout, QPushButton, QHBoxLayout
)
from views.add_contact_dialog import AddContactDialog

class ContactProfileDialog(QDialog):
    def __init__(self, parent=None, rowid=None):
        super().__init__(parent)
        self.setWindowTitle("Contact Profile")
        self.setMinimumWidth(400)
        self.rowid = rowid
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.info_labels = {}
        self.grid = QGridLayout()
        self.layout.addLayout(self.grid)

        self.build_ui()
        self.load_contact()

        btn_layout = QHBoxLayout()
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.clicked.connect(self.open_edit_dialog)
        btn_layout.addWidget(self.edit_btn)
        self.layout.addLayout(btn_layout)

    def build_ui(self):
        fields = [
            "Name", "WhatsApp", "Instagram", "Birthday", "Rating",
            "Last Club", "Visit Date", "Category", "Recent Visit", "Club Visits"
        ]
        self.field_keys = [
            "name", "whatsapp", "instagram", "birthday", "rating",
            "last_club", "visit_date", "category", "recent_visit", "club_visits"
        ]
        for i, label in enumerate(fields):
            self.grid.addWidget(QLabel(f"{label}:", self), i, 0)
            self.info_labels[label] = QLabel("-", self)
            self.grid.addWidget(self.info_labels[label], i, 1)

    def load_contact(self):
        conn = sqlite3.connect("clubbot.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name, whatsapp, instagram, birthday, rating, last_club, visit_date, category, recent_visit, club_visits FROM contacts WHERE rowid = ?", (self.rowid,))
        result = cursor.fetchone()
        conn.close()
        if result:
            for i, value in enumerate(result):
                label = list(self.info_labels.keys())[i]
                self.info_labels[label].setText(str(value) if value is not None else "-")

    def open_edit_dialog(self):
        conn = sqlite3.connect("clubbot.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name, whatsapp, birthday, instagram, rating, last_club, visit_date, category, recent_visit, club_visits FROM contacts WHERE rowid = ?", (self.rowid,))
        result = cursor.fetchone()
        conn.close()

        if result:
            contact_data = dict(zip([
                "name", "whatsapp", "birthday", "instagram", "rating", "last_club",
                "visit_date", "category", "recent_visit", "club_visits"
            ], result))
            contact_data["rowid"] = self.rowid
            dialog = AddContactDialog(self, contact_data)
            if dialog.exec_() == dialog.Accepted:
                self.load_contact()
