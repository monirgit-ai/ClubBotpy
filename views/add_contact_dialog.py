import sqlite3
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QSpinBox, QCheckBox, QMessageBox, QGridLayout
)

class AddContactDialog(QDialog):
    def __init__(self, parent=None, contact_data=None):
        super().__init__(parent)
        self.setWindowTitle("Add / Edit Contact")
        self.resize(500, 400)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.contact_data = contact_data or {}

        self.inputs = {}
        form_layout = QGridLayout()

        fields = [
            ("name", "Name"),
            ("whatsapp", "WhatsApp Number"),
            ("instagram", "Instagram"),
            ("birthday", "Birthday (YYYY-MM-DD)"),
            ("rating", "Rating"),
            ("last_club", "Last Club"),
            ("visit_date", "Date"),
            ("category", "Category"),
            ("recent_visit", "Most Recent Visit"),
            ("club_visits", "No. of Club Visits")
        ]

        for row, (key, label) in enumerate(fields):
            form_layout.addWidget(QLabel(label), row, 0)
            if key in ["rating", "club_visits"]:
                widget = QSpinBox()
                widget.setMaximum(100)
            else:
                widget = QLineEdit()
            self.inputs[key] = widget
            if key in self.contact_data:
                if isinstance(widget, QSpinBox):
                    widget.setValue(int(self.contact_data[key]))
                else:
                    widget.setText(str(self.contact_data[key]))
            form_layout.addWidget(widget, row, 1)

        self.layout.addLayout(form_layout)

        self.club_checkboxes = {}
        club_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun",
                      "Lio", "Tabu", "Dear D", "Reign", "Tape", "Maddox",
                      "Dolce", "Gallery", "Rex Rooms", "Selene"]

        club_layout = QGridLayout()
        for i, name in enumerate(club_names):
            key = name.lower().replace(' ', '_')
            checkbox = QCheckBox(name)
            if self.contact_data.get(key) in [1, "1", True]:
                checkbox.setChecked(True)
            self.club_checkboxes[key] = checkbox
            club_layout.addWidget(checkbox, i // 4, i % 4)

        self.layout.addWidget(QLabel("Visited Clubs:"))
        self.layout.addLayout(club_layout)

        save_btn = QPushButton("Save Contact")
        save_btn.clicked.connect(self.save_contact)
        self.layout.addWidget(save_btn)

    def save_contact(self):
        data = {key: inp.text() if isinstance(inp, QLineEdit) else inp.value()
                for key, inp in self.inputs.items()}
        for club, checkbox in self.club_checkboxes.items():
            data[club] = 1 if checkbox.isChecked() else 0

        try:
            conn = sqlite3.connect("clubbot.db")
            cursor = conn.cursor()
            if "rowid" in self.contact_data:
                set_clause = ", ".join([f"{k} = ?" for k in data])
                values = list(data.values())
                values.append(self.contact_data["rowid"])
                cursor.execute(f"UPDATE contacts SET {set_clause} WHERE rowid = ?", values)
            else:
                columns = ', '.join(data.keys())
                placeholders = ', '.join(['?'] * len(data))
                values = list(data.values())
                cursor.execute(f"INSERT INTO contacts ({columns}) VALUES ({placeholders})", values)
            conn.commit()
            conn.close()
            QMessageBox.information(self, "Success", "Contact saved successfully!")
            self.accept()
        except sqlite3.IntegrityError as e:
            QMessageBox.warning(self, "Error", f"Database error: {str(e)}")
        except Exception as ex:
            QMessageBox.warning(self, "Error", f"Unexpected error: {str(ex)}")
