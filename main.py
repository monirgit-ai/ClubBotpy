import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget
from PyQt5.QtGui import QIcon
from db.db_init import init_db

# Placeholder imports for views (will be implemented next)
from views.contacts_view import ContactsTab
from views.messages_view import MessagesTab
from views.campaign_view import CampaignTab
from views.reports_view import ReportsTab

class ClubBotApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ClubBot - WhatsApp Campaign Manager")
        self.setGeometry(200, 100, 1000, 600)
        self.setWindowIcon(QIcon("assets/icon.png"))

        init_db()  # Initialize database
        self.initUI()

    def initUI(self):
        tabs = QTabWidget()
        tabs.addTab(ContactsTab(), "Contacts")
        tabs.addTab(MessagesTab(), "Messages")
        tabs.addTab(CampaignTab(), "Campaigns")
        tabs.addTab(ReportsTab(), "Reports")
        self.setCentralWidget(tabs)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = ClubBotApp()
    main_window.show()
    sys.exit(app.exec_())
