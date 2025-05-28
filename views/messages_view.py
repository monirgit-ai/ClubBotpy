import os
import sqlite3
from PyQt5.QtWidgets import QHeaderView

from functools import partial
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QTextEdit, QPushButton, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QLabel, QMessageBox, QComboBox, QWidget as QW
)
from PyQt5.QtCore import Qt


class MessagesTab(QWidget):
    def __init__(self):
        super().__init__()
        self.editing_message_id = None
        self.setup_ui()
        self.load_message_types()
        self.load_messages()

    def setup_ui(self):
        layout = QVBoxLayout()

        self.filter_type_combo = QComboBox()
        self.filter_type_combo.addItem("All Types")
        self.filter_type_combo.currentIndexChanged.connect(self.load_messages)

        self.type_input = QLineEdit()
        self.type_input.setPlaceholderText("Message Type (e.g. Greeting, Follow-up)")
        layout.addWidget(self.type_input)

        self.content_input = QTextEdit()
        self.content_input.setPlaceholderText("Enter message content here. Use {Name} for personalization.")
        layout.addWidget(self.content_input)

        self.save_btn = QPushButton("Save Message Template")
        self.save_btn.clicked.connect(self.save_message)
        layout.addWidget(self.save_btn)

        layout.addWidget(QLabel("Filter by Type:"))
        layout.addWidget(self.filter_type_combo)

        self.message_table = QTableWidget()
        self.message_table.setColumnCount(3)
        self.message_table.setHorizontalHeaderLabels(["Type", "Content", "Actions"])
        header = self.message_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Type
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Content
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Actions

        self.message_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.message_table)

        self.setLayout(layout)

    def db_connection(self):
        return sqlite3.connect(os.path.join(os.path.dirname(__file__), "../db/clubbot.db"))

    def load_message_types(self):
        conn = self.db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT type FROM messages")
        types = cursor.fetchall()
        for t in types:
            self.filter_type_combo.addItem(t[0])
        conn.close()

    def load_messages(self):
        selected_type = self.filter_type_combo.currentText()
        conn = self.db_connection()
        cursor = conn.cursor()

        if selected_type == "All Types":
            cursor.execute("SELECT id, type, content FROM messages")
        else:
            cursor.execute("SELECT id, type, content FROM messages WHERE type = ?", (selected_type,))
        messages = cursor.fetchall()
        conn.close()

        self.message_table.setRowCount(0)
        for row_idx, (msg_id, msg_type, content) in enumerate(messages):
            self.message_table.insertRow(row_idx)
            self.message_table.setItem(row_idx, 0, QTableWidgetItem(msg_type))
            preview = content if len(content) < 40 else content[:40] + "..."
            self.message_table.setItem(row_idx, 1, QTableWidgetItem(preview))

            # Action buttons: Edit + Delete
            btn_layout = QHBoxLayout()
            btn_widget = QW()

            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(partial(self.load_for_edit, msg_id, msg_type, content))
            btn_layout.addWidget(edit_btn)

            delete_btn = QPushButton("Delete")
            delete_btn.clicked.connect(partial(self.delete_message, msg_id))
            btn_layout.addWidget(delete_btn)

            btn_layout.setContentsMargins(0, 0, 0, 0)
            btn_widget.setLayout(btn_layout)

            self.message_table.setCellWidget(row_idx, 2, btn_widget)

        self.message_table.resizeRowsToContents()

    def load_for_edit(self, msg_id, msg_type, content):
        self.editing_message_id = msg_id
        self.type_input.setText(msg_type)
        self.content_input.setText(content)
        self.save_btn.setText("Update Message")

    def save_message(self):
        msg_type = self.type_input.text().strip()
        msg_content = self.content_input.toPlainText().strip()

        if not msg_type or not msg_content:
            QMessageBox.warning(self, "Validation Error", "Both type and content are required.")
            return

        conn = self.db_connection()
        cursor = conn.cursor()

        if self.editing_message_id:
            cursor.execute("UPDATE messages SET type = ?, content = ? WHERE id = ?",
                           (msg_type, msg_content, self.editing_message_id))
        else:
            cursor.execute("INSERT INTO messages (type, content) VALUES (?, ?)", (msg_type, msg_content))

        conn.commit()
        conn.close()

        self.editing_message_id = None
        self.type_input.clear()
        self.content_input.clear()
        self.save_btn.setText("Save Message Template")
        self.filter_type_combo.clear()
        self.filter_type_combo.addItem("All Types")
        self.load_message_types()
        self.load_messages()

    def delete_message(self, msg_id):
        confirm = QMessageBox.question(self, "Confirm Delete", "Are you sure you want to delete this message?",
                                       QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            conn = self.db_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM messages WHERE id = ?", (msg_id,))
            conn.commit()
            conn.close()
            self.load_messages()
