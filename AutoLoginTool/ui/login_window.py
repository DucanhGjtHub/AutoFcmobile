import json
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QLineEdit, QMessageBox, QCheckBox)
from PyQt5.QtCore import Qt
from core.auth_manager import AuthManager

CREDENTIALS_FILE = "data/credentials.json"

class LoginWindow(QWidget):
    def __init__(self, on_success_callback):
        super().__init__()
        self.on_success_callback = on_success_callback
        self.auth_mgr = AuthManager()
        self.init_ui()
        self.load_credentials()

    def init_ui(self):
        self.setWindowTitle("Đăng nhập Hệ thống")
        self.resize(350, 230)
        
        layout = QVBoxLayout(self)
        
        lbl_title = QLabel("ĐĂNG NHẬP AUTO FC MOBILE")
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333; margin-bottom: 10px;")
        layout.addWidget(lbl_title)
        
        self.txt_email = QLineEdit()
        self.txt_email.setPlaceholderText("Email")
        layout.addWidget(self.txt_email)
        
        self.txt_password = QLineEdit()
        self.txt_password.setPlaceholderText("Mật khẩu")
        self.txt_password.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.txt_password)
        
        self.chk_remember = QCheckBox("Nhớ tài khoản và mật khẩu")
        layout.addWidget(self.chk_remember)
        
        self.btn_login = QPushButton("Đăng nhập")
        self.btn_login.setStyleSheet("background-color: #007bff; color: white; font-weight: bold; padding: 8px; margin-top: 10px;")
        self.btn_login.clicked.connect(self.do_login)
        layout.addWidget(self.btn_login)
        
        layout.addStretch()

    def load_credentials(self):
        if os.path.exists(CREDENTIALS_FILE):
            try:
                with open(CREDENTIALS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.txt_email.setText(data.get("email", ""))
                    self.txt_password.setText(data.get("password", ""))
                    self.chk_remember.setChecked(True)
            except:
                pass

    def do_login(self):
        email = self.txt_email.text().strip()
        password = self.txt_password.text().strip()
        
        if not email or not password:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập đầy đủ email và mật khẩu!")
            return
            
        self.btn_login.setText("Đang xử lý...")
        self.btn_login.setEnabled(False)
        
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import QCoreApplication
        QCoreApplication.processEvents()
        
        success, msg, role = self.auth_mgr.login(email, password)
        
        if success:
            if self.chk_remember.isChecked():
                os.makedirs("data", exist_ok=True)
                with open(CREDENTIALS_FILE, 'w', encoding='utf-8') as f:
                    json.dump({"email": email, "password": password}, f)
            else:
                if os.path.exists(CREDENTIALS_FILE):
                    os.remove(CREDENTIALS_FILE)

            QMessageBox.information(self, "Thành công", msg)
            self.on_success_callback(role, self.auth_mgr)
        else:
            QMessageBox.critical(self, "Lỗi đăng nhập", msg)
            self.btn_login.setText("Đăng nhập")
            self.btn_login.setEnabled(True)
