import os
import json
import sqlite3
import subprocess
import threading

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QTextEdit, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QCheckBox, QHBoxLayout, QMessageBox, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from functools import partial
import requests

class CampaignsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.selected_contacts = []
        self.selected_numbers = []
        self.contacts = []
        self.groups = []
        self.messages = []
        self.setup_ui()
        self.refresh_all()

    def db_connection(self):
        conn = sqlite3.connect(os.path.join(os.path.dirname(__file__), "../db/clubbot.db"), timeout=10)
        conn.execute("PRAGMA journal_mode=WAL")  # Enable write-ahead logging
        return conn

    def setup_ui(self):
        layout = QVBoxLayout()

        # Contact Filter
        contact_filter_layout = QHBoxLayout()
        self.contact_filter = QComboBox()
        self.contact_filter.addItem("-- No Filter --")
        self.contact_filter.addItem("Upcoming Birthdays")
        self.contact_filter.addItem("Rating 6+ (Artist Night)")
        self.contact_filter.currentIndexChanged.connect(self.filter_contacts)
        contact_filter_layout.addWidget(QLabel("Contact Filter"))
        contact_filter_layout.addWidget(self.contact_filter)

        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.refresh_all)
        contact_filter_layout.addWidget(refresh_btn)



        layout.addLayout(contact_filter_layout)

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

        # Console Output Area
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setStyleSheet("background-color: black; color: lime; font-family: Consolas;")
        self.console_output.setPlaceholderText("📜 Message logs will appear here...")
        layout.addWidget(self.console_output)

        # Buttons & Delay Inputs in One Row
        self.open_btn = QPushButton("Open WhatsApp in Chrome")
        self.send_btn = QPushButton("Send WhatsApp Messages")
        self.send_btn.clicked.connect(self.send_whatsapp_messages)
        self.open_btn.clicked.connect(self.open_whatsapp_browser)

        self.min_delay_input = QLineEdit()
        self.min_delay_input.setPlaceholderText("Min delay (sec)")
        self.max_delay_input = QLineEdit()
        self.max_delay_input.setPlaceholderText("Max delay (sec)")

        bottom_row = QHBoxLayout()
        bottom_row.addWidget(self.open_btn)
        bottom_row.addWidget(QLabel("Delay Range:"))
        bottom_row.addWidget(self.min_delay_input)
        bottom_row.addWidget(QLabel("to"))
        bottom_row.addWidget(self.max_delay_input)
        bottom_row.addWidget(self.send_btn)
        layout.addLayout(bottom_row)
        self.setLayout(layout)
        self.monthly_btn = QPushButton("📆 Start Monthly Campaign")
        self.monthly_btn.clicked.connect(self.start_monthly_campaign)
        bottom_row.addWidget(self.monthly_btn)

    def refresh_all(self):
        self.load_contacts()
        self.load_groups()
        self.load_messages()
        self.filter_contacts()

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
        self.message_type_filter.blockSignals(True)
        self.message_type_filter.clear()
        self.message_type_filter.addItem("-- All Types --")

        conn = self.db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, type, content FROM messages")
        self.messages = cursor.fetchall()
        conn.close()

        types = sorted(set(t for _, t, _ in self.messages))
        self.message_type_filter.addItems(types)

        self.populate_message_list()
        self.message_type_filter.blockSignals(False)

    def populate_message_list(self):
        self.message_list.setRowCount(0)
        selected_type = self.message_type_filter.currentText()

        row_index = 0
        for mid, mtype, mcontent in self.messages:
            if selected_type != "-- All Types --" and mtype != selected_type:
                continue

            self.message_list.insertRow(row_index)

            checkbox = QCheckBox()
            self.message_list.setCellWidget(row_index, 0, checkbox)

            preview = mcontent[:50] + ("..." if len(mcontent) > 50 else "")
            content_item = QTableWidgetItem(f"[{mtype}] {preview}")
            self.message_list.setItem(row_index, 1, content_item)

            if content_item:
                content_item.setData(Qt.UserRole, mid)

            row_index += 1

    def toggle_all_messages(self, state):
        for row in range(self.message_list.rowCount()):
            checkbox = self.message_list.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(state == Qt.Checked)

    def filter_contacts(self):
        selected = self.contact_filter.currentText()
        from datetime import datetime
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
        try:
            self.message_type_filter.blockSignals(True)
            self.populate_message_list()
            self.select_all_checkbox.setChecked(False)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Message filtering failed: {str(e)}")
        finally:
            self.message_type_filter.blockSignals(False)

    def log_delivery_report(self, number, status):
        try:
            conn = self.db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO delivery_report (whatsapp, status, logged_at)
                VALUES (?, ?, datetime('now'))
            """, (number, status))
            conn.commit()
            conn.close()
            self.console_output.append(f"📋 Report logged for {number} [{status}]")
        except Exception as e:
            self.console_output.append(f"⚠️ Failed to log report for {number}: {str(e)}")

    def open_whatsapp_browser(self):
        try:
            script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../sendswhatsapp.py'))
            subprocess.Popen(['python', script_path, '--open'])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not open WhatsApp: {str(e)}")

    def send_whatsapp_messages(self):
        try:
            selected_message_ids = []
            for row in range(self.message_list.rowCount()):
                checkbox = self.message_list.cellWidget(row, 0)
                if checkbox and checkbox.isChecked():
                    item = self.message_list.item(row, 1)
                    if item:
                        selected_message_ids.append(item.data(Qt.UserRole))

            if not self.selected_numbers or not selected_message_ids:
                QMessageBox.warning(self, "Warning", "Please select contacts and messages first.")
                return

            # Fetch messages
            conn = self.db_connection()
            cursor = conn.cursor()
            qmarks = ",".join("?" * len(selected_message_ids))
            cursor.execute(f"SELECT id, content FROM messages WHERE id IN ({qmarks})", selected_message_ids)
            id_to_message = {row[0]: row[1] for row in cursor.fetchall()}

            # Build message list
            numbers, names, messages, log_items = [], [], [], []
            for i, contact in enumerate(self.selected_contacts):
                contact_id = contact[0]
                number = self.selected_numbers[i]
                name = contact[1].split()[0] if contact[1] else ""

                cursor.execute("SELECT message_id FROM contact_message_log WHERE contact_id = ?", (contact_id,))
                sent_ids = {row[0] for row in cursor.fetchall()}
                available_ids = [mid for mid in selected_message_ids if mid not in sent_ids]
                if not available_ids:
                    available_ids = selected_message_ids

                if self.send_mode.currentText() == "Random Rotation":
                    import random
                    chosen_id = random.choice(available_ids)
                else:
                    chosen_id = available_ids[0]

                chosen_msg = id_to_message[chosen_id]
                personalized = chosen_msg.replace("{Name}", name)

                numbers.append(number)
                names.append(name)
                messages.append(personalized)
                log_items.append((contact_id, number, chosen_id))

                self.console_output.append(f"➡️ Prepared for {number}: {personalized[:60]}...")

            conn.close()

            # Save all to campaign_data.json
            temp_data = {
                "numbers": numbers,
                "names": names,
                "messages": messages,
                "mode": "Same",
                "min_delay": int(self.min_delay_input.text() or 1),
                "max_delay": int(self.max_delay_input.text() or 3)
            }
            temp_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../campaign_data.json'))
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(temp_data, f, ensure_ascii=False, indent=2)

            # Launch WhatsApp sender
            def run_sender():
                try:
                    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../sendswhatsapp.py'))
                    process = subprocess.Popen(
                        ['python', script_path, '--send'],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        encoding='utf-8',
                        errors='replace'
                    )

                    index = 0
                    for line in process.stdout:
                        line = line.strip()
                        self.console_output.append(line)

                        if "✅ Sent to" in line:
                            if index < len(log_items):
                                contact_id, number, message_id = log_items[index]
                                self.log_message_sent(contact_id, message_id)
                                self.log_delivery_report(number, "Sent")
                                index += 1
                        elif "❌" in line and index < len(log_items):
                            _, number, _ = log_items[index]
                            self.log_delivery_report(number, "Failed")
                            index += 1

                    self.console_output.append("🎉 Campaign completed.")
                except Exception as e:
                    self.console_output.append(f"❌ Error in sending thread: {str(e)}")

            threading.Thread(target=run_sender, daemon=True).start()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not send messages: {str(e)}")

    def log_message_sent(self, contact_id, message_id):
        try:
            conn = self.db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO contact_message_log (contact_id, message_id, sent_at)
                VALUES (?, ?, datetime('now'))
            """, (contact_id, message_id))
            conn.commit()
            conn.close()
            self.console_output.append(f"ℹ️ Logged message ID {message_id} for contact ID {contact_id}")
        except Exception as e:
            self.console_output.append(f"⚠️ Failed to log message for contact ID {contact_id}: {str(e)}")

    def start_monthly_campaign(self):
        try:
            # Select "1st Monthly Message" type
            index = self.message_type_filter.findText("1st Monthly Message")
            if index != -1:
                self.message_type_filter.setCurrentIndex(index)
                self.populate_message_list()
                self.select_all_checkbox.setChecked(True)

                # Optionally clear contact filter to include all
                self.contact_filter.setCurrentIndex(0)
                self.filter_contacts()

                confirm = QMessageBox.question(
                    self,
                    "Confirm Monthly Campaign",
                    "This will send unique 'Start of Month' messages to all selected contacts.\n\nProceed?",
                    QMessageBox.Yes | QMessageBox.No
                )

                if confirm == QMessageBox.Yes:
                    self.send_whatsapp_messages()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Monthly campaign setup failed: {str(e)}")


