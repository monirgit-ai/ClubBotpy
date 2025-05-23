import sqlite3
import threading
import time
import requests
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QListWidget,
    QPushButton, QMessageBox, QTextEdit
)

class CampaignTab(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.stop_flag = False
        self.setup_ui()
        self.setLayout(self.layout)

    def setup_ui(self):
        self.message_selector = QComboBox()
        self.contact_selector = QListWidget()
        self.contact_selector.setSelectionMode(QListWidget.MultiSelection)

        self.send_btn = QPushButton("Start Campaign")
        self.stop_btn = QPushButton("Stop Campaign")
        self.stop_btn.clicked.connect(self.stop_campaign)
        self.send_btn.clicked.connect(self.run_campaign)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)

        self.layout.addWidget(QLabel("Select Message Template:"))
        self.layout.addWidget(self.message_selector)
        self.layout.addWidget(QLabel("Select Contacts:"))
        self.layout.addWidget(self.contact_selector)
        self.layout.addWidget(self.send_btn)
        self.layout.addWidget(self.stop_btn)
        self.layout.addWidget(QLabel("Campaign Log:"))
        self.layout.addWidget(self.log_box)

        self.load_message_options()
        self.load_contact_options()

    def load_message_options(self):
        self.message_selector.clear()
        conn = sqlite3.connect("clubbot.db")
        cursor = conn.cursor()
        cursor.execute("SELECT content FROM messages")
        for row in cursor.fetchall():
            self.message_selector.addItem(row[0])
        conn.close()

    def load_contact_options(self):
        self.contact_selector.clear()
        conn = sqlite3.connect("clubbot.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name, whatsapp FROM contacts")
        for row in cursor.fetchall():
            self.contact_selector.addItem(f"{row[0]} | {row[1]}")
        conn.close()

    def run_campaign(self):
        self.stop_flag = False
        message_template = self.message_selector.currentText()
        selected_items = self.contact_selector.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Contacts Selected", "Please select at least one contact.")
            return
        threading.Thread(target=self.send_messages, args=(message_template, selected_items)).start()

    def stop_campaign(self):
        self.stop_flag = True
        self.log_box.append("\n[!] Campaign stopped by user.")

    def send_messages(self, template, items):
        for item in items:
            if self.stop_flag:
                break

            display_text = item.text()
            try:
                name, number = display_text.split(" | ")
                personalized_msg = template.replace("{Name}", name)

                # Send via Flask API
                response = requests.post("http://127.0.0.1:5000/send-message", json={
                    "number": number,
                    "message": personalized_msg
                }, timeout=60)

                status = 'sent' if response.ok and response.json().get("status") == "sent" else 'failed'

                conn = sqlite3.connect("clubbot.db")
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM contacts WHERE whatsapp = ?", (number,))
                contact = cursor.fetchone()
                contact_id = contact[0] if contact else None
                cursor.execute("INSERT INTO campaign_reports (contact_id, message, status, sent_date) VALUES (?, ?, ?, ?)",
                               (contact_id, personalized_msg, status, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                conn.commit()
                conn.close()

                if status == 'sent':
                    self.log_box.append(f"[✓] Sent to {name} ({number})")
                else:
                    self.log_box.append(f"[✗] Failed to send to {name} ({number})")

            except Exception as e:
                self.log_box.append(f"[✗] Error for {display_text}: {str(e)}")
                if 'conn' in locals():
                    cursor.execute("INSERT INTO campaign_reports (contact_id, message, status, sent_date) VALUES (?, ?, ?, ?)",
                                   (None, personalized_msg, 'failed', datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                    conn.commit()
                    conn.close()

        self.log_box.append("\n[*] Campaign completed.")
