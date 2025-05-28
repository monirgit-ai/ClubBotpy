import os
import sqlite3
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QLabel
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QBrush

class ReportsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setup_ui()
        self.setLayout(self.layout)

    def db_connection(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        return sqlite3.connect(os.path.join(base_dir, "../db/clubbot.db"))

    def setup_ui(self):
        self.reports_table = QTableWidget()
        self.reports_table.setColumnCount(4)
        self.reports_table.setHorizontalHeaderLabels(["Contact Name", "Message", "Status", "Date"])
        self.reports_table.horizontalHeader().setStretchLastSection(True)
        self.reports_table.setWordWrap(True)

        self.refresh_btn = QPushButton("Refresh Reports")
        self.refresh_btn.clicked.connect(self.load_reports)

        self.layout.addWidget(QLabel("📊 Campaign Report Viewer"))
        self.layout.addWidget(self.reports_table)
        self.layout.addWidget(self.refresh_btn)

        self.load_reports()

    def load_reports(self):
        try:
            conn = self.db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT c.name, r.message, r.status, r.sent_date
                FROM campaign_reports r
                LEFT JOIN contacts c ON r.contact_id = c.rowid
                ORDER BY r.sent_date DESC
            ''')
            rows = cursor.fetchall()
            conn.close()
        except Exception as e:
            self.reports_table.setRowCount(0)
            self.reports_table.setColumnCount(1)
            self.reports_table.setHorizontalHeaderLabels(["Error"])
            self.reports_table.insertRow(0)
            self.reports_table.setItem(0, 0, QTableWidgetItem(f"Error: {str(e)}"))
            return

        self.reports_table.setRowCount(len(rows))

        for i, (name, message, status, sent_date) in enumerate(rows):
            self.reports_table.setItem(i, 0, QTableWidgetItem(name or "Unknown"))

            msg_item = QTableWidgetItem(message)
            msg_item.setFlags(Qt.ItemIsEnabled)
            self.reports_table.setItem(i, 1, msg_item)

            status_item = QTableWidgetItem(status)
            if status.lower() == "sent":
                status_item.setForeground(QBrush(QColor("green")))
            elif status.lower() == "failed":
                status_item.setForeground(QBrush(QColor("red")))
            else:
                status_item.setForeground(QBrush(QColor("orange")))
            self.reports_table.setItem(i, 2, status_item)

            date_item = QTableWidgetItem(sent_date)
            date_item.setTextAlignment(Qt.AlignCenter)
            self.reports_table.setItem(i, 3, date_item)
