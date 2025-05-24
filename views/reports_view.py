import sqlite3
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QLabel
)

class ReportsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setup_ui()
        self.setLayout(self.layout)

    def setup_ui(self):
        self.reports_table = QTableWidget()
        self.reports_table.setColumnCount(4)
        self.reports_table.setHorizontalHeaderLabels(["Contact Name", "Message", "Status", "Date"])

        self.refresh_btn = QPushButton("Refresh Reports")
        self.refresh_btn.clicked.connect(self.load_reports)

        self.layout.addWidget(QLabel("Campaign Report Viewer"))
        self.layout.addWidget(self.reports_table)
        self.layout.addWidget(self.refresh_btn)

        self.load_reports()

    def load_reports(self):
        conn = sqlite3.connect("db/clubbot.db")
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.name, r.message, r.status, r.sent_date
            FROM campaign_reports r
            LEFT JOIN contacts c ON r.contact_id = c.rowid
            ORDER BY r.sent_date DESC
        ''')
        rows = cursor.fetchall()
        conn.close()

        self.reports_table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, value in enumerate(row):
                self.reports_table.setItem(i, j, QTableWidgetItem(str(value)))
