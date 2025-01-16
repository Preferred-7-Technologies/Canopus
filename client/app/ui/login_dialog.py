from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, 
                           QLineEdit, QPushButton, QLabel)
from PyQt5.QtCore import pyqtSignal
import logging
from ..core.api_client import APIClient

logger = logging.getLogger(__name__)

class LoginDialog(QDialog):
    login_successful = pyqtSignal(dict)

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.api_client = APIClient(config)
        
        self.setWindowTitle("Login to Canopus")
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        self.username = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: red")
        
        form_layout.addRow("Username:", self.username)
        form_layout.addRow("Password:", self.password)
        
        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.handle_login)
        
        layout.addLayout(form_layout)
        layout.addWidget(self.error_label)
        layout.addWidget(self.login_button)

    async def handle_login(self):
        try:
            credentials = {
                "username": self.username.text(),
                "password": self.password.text()
            }
            
            async with self.api_client as client:
                if await client.authenticate(credentials):
                    self.login_successful.emit({
                        "token": client.token,
                        "username": credentials["username"]
                    })
                    self.accept()
                else:
                    self.error_label.setText("Invalid credentials")
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            self.error_label.setText("Login failed. Please try again.")
