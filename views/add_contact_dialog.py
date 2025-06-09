import sqlite3
import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QSpinBox, QMessageBox, QGridLayout, QWidget
)
from PyQt5.QtCore import Qt

class AddContactDialog(QDialog):
    def __init__(self, parent=None, contact_data=None):
        super().__init__(parent)
        self.setWindowTitle("Add / Edit Contact")
        self.resize(700, 600)
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
                widget.setMinimum(0)
            else:
                widget = QLineEdit()
            self.inputs[key] = widget
            if key in self.contact_data and self.contact_data[key] is not None:
                if isinstance(widget, QSpinBox):
                    try:
                        widget.setValue(int(self.contact_data[key]))
                    except (ValueError, TypeError):
                        widget.setValue(0)
                else:
                    widget.setText(str(self.contact_data[key]))
            form_layout.addWidget(widget, row, 1)

        self.layout.addLayout(form_layout)

        self.week_days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        self.club_names = [
            "Cirque Le Soir", "Madox", "Tabu", "Leo", "Reign", "Tape",
            "Dear Darling", "The Box", "Lio", "Dolce", "Gallery", "Rex Rooms", "Selene"
        ]
        self.club_names.sort()

        self.layout.addWidget(QLabel("Club Visit Frequency:"))
        self.club_visit_grid = QGridLayout()

        for col, day in enumerate(self.week_days):
            day_label = QLabel(day)
            day_label.setAlignment(Qt.AlignCenter)
            self.club_visit_grid.addWidget(day_label, 0, col + 1)

        self.club_day_inputs = {}
        for row, club in enumerate(self.club_names):
            # NO special handling for "Dear Darling" here.
            # This will consistently convert all club names like "Dear Darling" -> "dear_darling"
            club_key = club.lower().replace(' ', '_').replace('.', '')

            self.club_day_inputs[club_key] = {}

            club_label = QLabel(club)
            self.club_visit_grid.addWidget(club_label, row + 1, 0)

            for col, day in enumerate(self.week_days):
                day_key = day.lower()
                spin_box = QSpinBox()
                spin_box.setMinimum(0)
                spin_box.setMaximum(99)
                spin_box.setValue(0)

                column_name = f"{club_key}_{day_key}"

                if column_name in self.contact_data and self.contact_data[column_name] is not None:
                    try:
                        spin_box.setValue(int(self.contact_data[column_name]))
                    except (ValueError, TypeError):
                        spin_box.setValue(0)

                self.club_day_inputs[club_key][day_key] = spin_box
                self.club_visit_grid.addWidget(spin_box, row + 1, col + 1)

        self.layout.addLayout(self.club_visit_grid)

        save_btn = QPushButton("Save Contact")
        save_btn.clicked.connect(self.save_contact)
        self.layout.addWidget(save_btn)

    def db_connection(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, "..", "db", "clubbot.db")
        return sqlite3.connect(db_path)

    def save_contact(self):
        data = {key: inp.text() if isinstance(inp, QLineEdit) else inp.value()
                for key, inp in self.inputs.items()}

        for club_key, day_inputs in self.club_day_inputs.items():
            for day_key, spin_box in day_inputs.items():
                column_name = f"{club_key}_{day_key}"
                data[column_name] = spin_box.value()

        conn = None
        try:
            conn = self.db_connection()
            cursor = conn.cursor()

            if "rowid" in self.contact_data:
                set_clause = ", ".join([f"{k} = ?" for k in data.keys()])
                values = list(data.values())
                values.append(self.contact_data["rowid"])
                cursor.execute(f"UPDATE contacts SET {set_clause} WHERE rowid = ?", values)
            else:
                columns = ', '.join(data.keys())
                placeholders = ', '.join(['?'] * len(data))
                values = list(data.values())
                cursor.execute(f"INSERT INTO contacts ({columns}) VALUES ({placeholders})", values)

            conn.commit()
            QMessageBox.information(self, "Success", "Contact saved successfully!")
            self.accept()
        except sqlite3.IntegrityError as e:
            QMessageBox.warning(self, "Database Error",
                                f"A database integrity error occurred, likely due to a duplicate WhatsApp number: {str(e)}")
        except sqlite3.Error as e:
            QMessageBox.warning(self, "Database Error", f"An SQLite error occurred: {str(e)}")
        except Exception as ex:
            QMessageBox.warning(self, "Unexpected Error", f"An unexpected error occurred: {str(ex)}")
        finally:
            if conn:
                conn.close()

