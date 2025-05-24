import sqlite3
from functools import partial
import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QMessageBox, QComboBox, QCheckBox
)
from PyQt5.QtCore import Qt

from PyQt5.QtWidgets import QInputDialog


class GroupManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Group Manager")
        self.setMinimumSize(800, 500)
        self.layout = QVBoxLayout()

        self.group_table = QTableWidget()
        self.group_table.setColumnCount(4)
        self.group_table.setHorizontalHeaderLabels(["Group Name", "# Contacts", "Edit", "Status"])
        self.load_group_summary()
        self.layout.addWidget(self.group_table)
        self.setLayout(self.layout)

        self.group_select = QComboBox()
        self.group_select.currentIndexChanged.connect(self.load_group_contacts)

        self.group_name_input = QLineEdit()
        self.group_name_input.setPlaceholderText("Enter Group Name")
        self.create_group_btn = QPushButton("Create Group")
        self.create_group_btn.clicked.connect(self.create_group)
        self.editing_group_id = None

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
        select_layout = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        deselect_all_btn = QPushButton("Deselect All")
        select_all_btn.clicked.connect(self.select_all_contacts)
        deselect_all_btn.clicked.connect(self.deselect_all_contacts)
        select_layout.addWidget(select_all_btn)
        select_layout.addWidget(deselect_all_btn)
        self.layout.addLayout(select_layout)

        self.layout.addWidget(self.contacts_table)

        self.load_group_summary()
        self.load_contacts()

    from PyQt5.QtWidgets import QInputDialog

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
            self.load_group_summary()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Duplicate", "Group with this name already exists.")
        finally:
            conn.close()

    def update_group(self):
        name = self.group_name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Input Error", "Group name cannot be empty.")
            return
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), "../db/clubbot.db"))
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE groups SET name = ? WHERE id = ?", (name, self.editing_group_id))
            conn.commit()
            self.group_name_input.clear()
            self.editing_group_id = None
            self.create_group_btn.setText("Create Group")
            self.create_group_btn.clicked.disconnect()
            self.create_group_btn.clicked.connect(self.create_group)
            self.load_group_summary()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Duplicate", "Group with this name already exists.")
        finally:
            conn.close()

    def load_group_summary(self):
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), "../db/clubbot.db"))
        cursor = conn.cursor()
        cursor.execute("""
            SELECT g.id, g.name, g.status, COUNT(cgm.contact_id) as total
            FROM groups g
            LEFT JOIN contact_group_map cgm ON g.id = cgm.group_id
            GROUP BY g.id, g.name, g.status
        """)
        rows = cursor.fetchall()
        self.group_table.setRowCount(0)
        for i, (gid, name, status, total) in enumerate(rows):
            self.group_table.insertRow(i)
            self.group_table.setItem(i, 0, QTableWidgetItem(name))
            self.group_table.setItem(i, 1, QTableWidgetItem(str(total)))

            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(partial(self.edit_group_dialog, gid, name))
            self.group_table.setCellWidget(i, 2, edit_btn)

            status_toggle = QPushButton("Deactivate" if status == "active" else "Activate")
            status_toggle.clicked.connect(partial(self.toggle_group_status_by_id, gid, status))
            self.group_table.setCellWidget(i, 3, status_toggle)
        conn.close()

        if hasattr(self, 'group_select'):
            self.group_select.clear()
            conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), "../db/clubbot.db"))
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, status FROM groups")
            self.groups = cursor.fetchall()
            for group in self.groups:
                self.group_select.addItem(f"{group[1]} ({group[2]})", group[0])
            conn.close()

    def edit_group_dialog(self, group_id, current_name):
        self.editing_group_id = group_id
        self.group_select.setCurrentIndex(self.group_select.findData(group_id))
        self.group_name_input.setText(current_name)
        self.create_group_btn.setText("Update Group")
        self.create_group_btn.clicked.disconnect()
        self.create_group_btn.clicked.connect(self.update_group)
        self.load_contacts()

    def toggle_group_status_by_id(self, group_id, current_status):
        new_status = "inactive" if current_status == "active" else "active"
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), "../db/clubbot.db"))
        cursor = conn.cursor()
        cursor.execute("UPDATE groups SET status = ? WHERE id = ?", (new_status, group_id))
        conn.commit()
        conn.close()
        self.load_group_summary()
        self.load_group_summary()

    def toggle_group_status(self):
        index = self.group_select.currentIndex()
        if index < 0:
            return
        group_id = self.group_select.itemData(index)
        current_status = self.groups[index][2]
        new_status = "inactive" if current_status == "active" else "active"
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), "../db/clubbot.db"))
        cursor = conn.cursor()
        cursor.execute("UPDATE groups SET status = ? WHERE id = ?", (new_status, group_id))
        conn.commit()
        conn.close()
        self.load_groups()

    def load_contacts(self):
        search = self.search_input.text().lower()
        rating_filter = self.rating_filter.currentText()

        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), "../db/clubbot.db"))
        cursor = conn.cursor()

        # Determine selected group
        group_id = None
        if hasattr(self, 'editing_group_id') and self.editing_group_id:
            group_id = self.editing_group_id
        elif hasattr(self, 'group_select') and self.group_select.currentIndex() >= 0:
            group_id = self.group_select.itemData(self.group_select.currentIndex())

        # Fetch all contacts
        cursor.execute("SELECT rowid, name, whatsapp, rating FROM contacts")
        all_contacts = cursor.fetchall()

        # Fetch contacts already in group
        assigned_ids = set()
        if group_id:
            cursor.execute("SELECT contact_id FROM contact_group_map WHERE group_id = ?", (group_id,))
            assigned_ids = {row[0] for row in cursor.fetchall()}

        conn.close()

        filtered = []
        for r in all_contacts:
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
            if cid in assigned_ids:
                checkbox.setChecked(True)
            checkbox.stateChanged.connect(partial(self.toggle_contact_group_assignment, cid))
            self.contacts_table.setCellWidget(i, 3, checkbox)

    def toggle_contact_group_assignment(self, contact_id, state):
        index = self.group_select.currentIndex()
        if index < 0:
            return
        group_id = self.group_select.itemData(index)

        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), "../db/clubbot.db"))
        cursor = conn.cursor()

        if state == Qt.Checked:
            cursor.execute("INSERT OR IGNORE INTO contact_group_map (contact_id, group_id) VALUES (?, ?)",
                           (contact_id, group_id))
        else:
            cursor.execute("DELETE FROM contact_group_map WHERE contact_id = ? AND group_id = ?",
                           (contact_id, group_id))

        conn.commit()
        conn.close()

    def select_all_contacts(self):
        for row in range(self.contacts_table.rowCount()):
            checkbox = self.contacts_table.cellWidget(row, 3)
            if checkbox:
                checkbox.setChecked(True)

    def deselect_all_contacts(self):
        for row in range(self.contacts_table.rowCount()):
            checkbox = self.contacts_table.cellWidget(row, 3)
            if checkbox:
                checkbox.setChecked(False)

    def load_group_contacts(self):
        self.load_contacts()

    def open_group_manager(self):
        from views.group_manager import GroupManagerDialog
        dialog = GroupManagerDialog(self)
        dialog.exec_()
