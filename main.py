import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QMessageBox, QDialog # Added QDialog
from PyQt5.QtGui import QIcon
from db.db_init import init_db

# Import your view tabs
from views.contacts_view2 import ContactsTab
from views.messages_view import MessagesTab
from views.campaign_view import CampaignsTab
from views.reports_view import ReportsTab

# Import the new login and user management components
from views.login_dialog import LoginDialog
from views.user_management_tab import UserManagementTab

class ClubBotApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ClubBot - WhatsApp Campaign Manager")
        self.setGeometry(200, 100, 1000, 600)
        self.setWindowIcon(QIcon("icon.png")) # Assuming you have an icon.png in your root directory

        init_db()  # Initialize database schema (including the 'users' table)

        self.logged_in_user_id = None
        self.logged_in_username = None
        self.logged_in_role = None

        self.show_login_and_init_ui()

    def show_login_and_init_ui(self):
        """Displays the login dialog and initializes the main UI upon successful login."""
        login_dialog = LoginDialog(self)
        if login_dialog.exec_() == QDialog.Accepted:
            # Login successful, store user info
            self.logged_in_user_id = login_dialog.logged_in_user_id
            self.logged_in_username = login_dialog.logged_in_username
            self.logged_in_role = login_dialog.logged_in_role
            self.setWindowTitle(f"ClubBot - WhatsApp Campaign Manager (Logged in as: {self.logged_in_username})")
            self.initUI() # Initialize main application UI
            self.showMaximized() # Optionally start maximized
        else:
            # Login failed or cancelled, exit application
            QMessageBox.information(self, "Login Cancelled", "Application will close.")
            QApplication.quit()

    def initUI(self):
        """Initializes the main application tabs based on user role."""
        tabs = QTabWidget()

        # Always add core tabs
        tabs.addTab(CampaignsTab(), "Campaign")
        tabs.addTab(ContactsTab(), "Contacts")
        tabs.addTab(MessagesTab(), "Messages")
        tabs.addTab(ReportsTab(), "Reports")

        # Conditionally add User Management tab for admins
        if self.logged_in_role == 'admin':
            tabs.addTab(UserManagementTab(), "Manage Users")
            # Removed: QMessageBox.information(self, "Admin Access", "Logged in as Admin. 'Manage Users' tab is available.")

        self.setCentralWidget(tabs)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = ClubBotApp()
    # The main_window will be shown within show_login_and_init_ui after successful login.
    # No need for main_window.show() here.
    sys.exit(app.exec_())
