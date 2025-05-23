import sqlite3
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QTextEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox
)

class MessagesTab(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        self.setup_ui()
        self.setLayout(self.layout)

    def setup_ui(self):
        self.message_type_input = QLineEdit()
        self.message_type_input.setPlaceholderText("Message Type (e.g. Greeting, Follow-up)")

        self.message_content_input = QTextEdit()
        self.message_content_input.setPlaceholderText("Enter message content here. Use {Name} for personalization.")

        add_btn = QPushButton("Save Message Template")
        add_btn.clicked.connect(self.save_message_template)

        self.layout.addWidget(self.message_type_input)
        self.layout.addWidget(self.message_content_input)
        self.layout.addWidget(add_btn)

        self.message_table = QTableWidget()
        self.message_table.setColumnCount(2)
        self.message_table.setHorizontalHeaderLabels(["Type", "Content"])
        self.layout.addWidget(self.message_table)

        self.load_messages()

    def save_message_template(self):
        msg_type = self.message_type_input.text()
        content = self.message_content_input.toPlainText()

        if not msg_type or not content:
            QMessageBox.warning(self, "Input Error", "Both type and content are required.")
            return

        conn = sqlite3.connect("clubbot.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO messages (type, content) VALUES (?, ?)", (msg_type, content))
        conn.commit()
        conn.close()

        self.load_messages()
        self.message_type_input.clear()
        self.message_content_input.clear()

    def load_messages(self):
        conn = sqlite3.connect("clubbot.db")
        cursor = conn.cursor()
        cursor.execute("SELECT type, content FROM messages")
        rows = cursor.fetchall()
        conn.close()

        self.message_table.setRowCount(len(rows))
        for i, (msg_type, content) in enumerate(rows):
            self.message_table.setItem(i, 0, QTableWidgetItem(msg_type))
            self.message_table.setItem(i, 1, QTableWidgetItem(content))
