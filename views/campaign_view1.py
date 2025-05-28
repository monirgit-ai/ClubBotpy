import os
import json
import sqlite3
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QTextEdit, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QCheckBox, QHBoxLayout, QMessageBox, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from functools import partial
import requests
import subprocess
import threading
import time
import sys

class CampaignsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_contacts = []
        self.selected_numbers = []
        self.contacts = []
        self.groups = []
        self.messages = []
        self.setup_ui()
        self.load_contacts()
        self.load_groups()
        self.load_messages()

    def db_connection(self):
        return sqlite3.connect(os.path.join(os.path.dirname(__file__), "../db/clubbot.db"))

    def setup_ui(self):
        layout = QVBoxLayout()

        # Contact Filter
        self.contact_filter = QComboBox()
        self.contact_filter.addItem("-- No Filter --")
        self.contact_filter.addItem("Upcoming Birthdays")
        self.contact_filter.addItem("Rating 6+ (Artist Night)")
        self.contact_filter.currentIndexChanged.connect(self.filter_contacts)
        layout.addWidget(QLabel("Contact Filter"))
        layout.addWidget(self.contact_filter)

        # WhatsApp Numbers Display (readonly)
        self.numbers_display = QLineEdit()
        self.numbers_display.setReadOnly(True)
        layout.addWidget(QLabel("Numbers (autofilled by filter)"))
        layout.addWidget(self.numbers_display)

        # Send Mode
        self.send_mode = QComboBox()
        self.send_mode.addItems(["Same Message to All", "Random Rotation"])
        layout.addWidget(QLabel("Select Sending Mode"))
        layout.addWidget(self.send_mode)

        # Message Type Filter
        self.message_type_filter = QComboBox()
        self.message_type_filter.addItem("-- All Types --")
        self.message_type_filter.currentIndexChanged.connect(self.filter_messages)
        layout.addWidget(QLabel("Select Message Type"))
        layout.addWidget(self.message_type_filter)

        # Message List with Select All
        msg_top_layout = QHBoxLayout()
        self.select_all_checkbox = QCheckBox("Select All Messages")
        self.select_all_checkbox.stateChanged.connect(self.toggle_all_messages)
        msg_top_layout.addWidget(self.select_all_checkbox)
        layout.addLayout(msg_top_layout)

        self.message_list = QTableWidget()
        self.message_list.setColumnCount(2)
        self.message_list.setHorizontalHeaderLabels(["Select", "Message"])
        self.message_list.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.message_list)

        # Send Button
        self.send_btn = QPushButton("Send WhatsApp Messages")
        self.send_btn.clicked.connect(self.send_campaign)
        open_browser_btn = QPushButton("Open WhatsApp in Chrome")
        open_browser_btn.clicked.connect(self.open_whatsapp_chrome)
        layout.addWidget(open_browser_btn)
        layout.addWidget(self.send_btn)

        self.setLayout(layout)

    def open_whatsapp_chrome(self):
        try:
            script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../flask/app.py"))
            python_exec = sys.executable  # path to current Python interpreter
            subprocess.Popen([python_exec, script_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not launch app.py: {str(e)}")

    def load_contacts(self):
        conn = self.db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT rowid, name, whatsapp, birthday, rating FROM contacts")
        self.contacts = cursor.fetchall()
        conn.close()

    def load_groups(self):
        conn = self.db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM groups")
        self.groups = cursor.fetchall()
        for gid, gname in self.groups:
            self.contact_filter.addItem(f"Group: {gname}", gid)
        conn.close()

    def load_messages(self):
        conn = self.db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, type, content FROM messages")
        self.messages = cursor.fetchall()
        conn.close()

        self.message_type_filter.addItems(sorted(set([str(t) for _, t, _ in self.messages if t])))
        self.populate_message_list()

    def populate_message_list(self):
        self.message_list.setRowCount(0)
        selected_type = self.message_type_filter.currentText()
        for i, (mid, mtype, mcontent) in enumerate(self.messages):
            if selected_type != "-- All Types --" and mtype != selected_type:
                continue
            row_index = self.message_list.rowCount()
            self.message_list.insertRow(row_index)
            checkbox = QCheckBox()
            self.message_list.setCellWidget(row_index, 0, checkbox)
            preview = mcontent[:50] + ("..." if len(mcontent) > 50 else "")
            self.message_list.setItem(row_index, 1, QTableWidgetItem(f"[{mtype}] {preview}"))
            self.message_list.item(row_index, 1).setData(Qt.UserRole, mid)

    def toggle_all_messages(self, state):
        for row in range(self.message_list.rowCount()):
            checkbox = self.message_list.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(state == Qt.Checked)

    def filter_contacts(self):
        selected = self.contact_filter.currentText()
        from datetime import datetime, timedelta
        today = datetime.now()
        filtered = []

        if selected == "Upcoming Birthdays":
            for c in self.contacts:
                if not c[3]: continue
                try:
                    bday = datetime.strptime(c[3], "%Y-%m-%d")
                    bday_this_year = bday.replace(year=today.year)
                    days = (bday_this_year - today).days
                    if 0 <= days <= 21:
                        filtered.append(c)
                except:
                    continue
        elif selected == "Rating 6+ (Artist Night)":
            filtered = [c for c in self.contacts if c[4] and int(c[4]) >= 6]
        elif selected.startswith("Group: "):
            group_name = selected[7:]
            group_id = next((gid for gid, gname in self.groups if gname == group_name), None)
            if group_id:
                conn = self.db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT contact_id FROM contact_group_map WHERE group_id = ?", (group_id,))
                contact_ids = {row[0] for row in cursor.fetchall()}
                filtered = [c for c in self.contacts if c[0] in contact_ids]
                conn.close()
        else:
            filtered = self.contacts[:]

        self.selected_contacts = filtered
        self.selected_numbers = [c[2] for c in filtered if c[2]]
        self.numbers_display.setText(", ".join([c[1] for c in filtered]))

    def filter_messages(self):
        self.populate_message_list()
        self.select_all_checkbox.setChecked(False)

    def start_flask_if_needed(self):
        def _check_and_launch():
            try:
                r = requests.get("http://127.0.0.1:5000")
                if r.status_code == 200:
                    print("✅ Flask is already running.")
                    return
            except:
                print("🚀 Starting Flask server...")
                subprocess.Popen(["python", "../flask/app.py"], cwd=os.path.dirname(__file__))

            for _ in range(20):  # wait up to 20 seconds
                try:
                    r = requests.get("http://127.0.0.1:5000")
                    if r.status_code == 200:
                        print("✅ Flask started successfully.")
                        return
                except:
                    pass
                time.sleep(1)

            QMessageBox.warning(self, "Timeout", "Failed to connect to Flask after 20 seconds.")

        threading.Thread(target=_check_and_launch).start()

    def open_whatsapp_browser(self):
        try:
            requests.get("http://127.0.0.1:5000/open-browser")
        except Exception as e:
            QMessageBox.critical(self, "Flask Error", f"Could not open browser: {str(e)}")

    def send_campaign(self):
        self.start_flask_if_needed()

        # Get selected messages
        message_ids = [self.message_list.item(r, 1).data(Qt.UserRole)
                       for r in range(self.message_list.rowCount())
                       if self.message_list.cellWidget(r, 0).isChecked()]

        if not self.selected_numbers or not message_ids:
            QMessageBox.warning(self, "Missing Info", "Please select contacts and messages.")
            return

        # Use first message (or rotate if random)
        conn = self.db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT content FROM messages WHERE id IN ({})".format(",".join(["?"] * len(message_ids))),
                       message_ids)
        messages = [row[0] for row in cursor.fetchall()]
        conn.close()

        success_count = 0
        for idx, number in enumerate(self.selected_numbers):
            msg = messages[0] if self.send_mode.currentText().startswith("Same") else messages[idx % len(messages)]

            try:
                r = requests.post("http://127.0.0.1:5000/send-message", json={"number": number, "message": msg},
                                  timeout=60)
                if r.status_code == 200:
                    print(f"✅ Sent to {number}")
                    success_count += 1
                else:
                    print(f"❌ Failed for {number}: {r.text}")
            except Exception as e:
                print(f"❌ Error for {number}: {e}")

        QMessageBox.information(self, "Done", f"{success_count} messages sent.")