from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QTableWidget, QTableWidgetItem, 
                             QMessageBox, QInputDialog, QHeaderView)
from PyQt5.QtCore import Qt

class AdminWindow(QMainWindow):
    def __init__(self, auth_mgr):
        super().__init__()
        self.auth_mgr = auth_mgr
        self.setWindowTitle("Admin Dashboard - Quản lý Tài Khoản")
        self.resize(900, 600)
        self.init_ui()
        self.load_users()
        
    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        lbl_title = QLabel("DANH SÁCH TÀI KHOẢN (USER)")
        lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(lbl_title)
        
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["UID", "Email", "Role", "Giới hạn thiết bị", "Đã dùng", "Trạng thái", "Hành động"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)
        
        btn_layout = QHBoxLayout()
        btn_refresh = QPushButton("Làm mới danh sách")
        btn_refresh.setStyleSheet("padding: 8px;")
        btn_refresh.clicked.connect(self.load_users)
        btn_layout.addWidget(btn_refresh)
        
        btn_add = QPushButton("Tạo tài khoản mới")
        btn_add.setStyleSheet("background-color: #28a745; color: white; padding: 8px; font-weight: bold;")
        btn_add.clicked.connect(self.create_user)
        btn_layout.addWidget(btn_add)
        
        layout.addLayout(btn_layout)

    def load_users(self):
        users = self.auth_mgr.get_all_users()
        if not isinstance(users, dict):
            users = {}
        self.table.setRowCount(len(users))
        
        row = 0
        self.user_uids = []
        for uid, data in users.items():
            if not isinstance(data, dict):
                continue
                
            self.user_uids.append(uid)
            email = data.get("email", "Unknown")
            role = data.get("role", "user")
            limit = data.get("devices", 1)
            hwids = data.get("registered_hwids", {})
            used = len(hwids)
            locked = data.get("locked", False)
            
            status = "Bị khóa" if locked else "Hoạt động"
            
            self.table.setItem(row, 0, QTableWidgetItem(uid[:8] + "..."))
            self.table.setItem(row, 1, QTableWidgetItem(email))
            self.table.setItem(row, 2, QTableWidgetItem(role))
            self.table.setItem(row, 3, QTableWidgetItem(str(limit)))
            self.table.setItem(row, 4, QTableWidgetItem(f"{used}/{limit}"))
            
            item_status = QTableWidgetItem(status)
            if locked:
                item_status.setForeground(Qt.red)
            else:
                item_status.setForeground(Qt.darkGreen)
            self.table.setItem(row, 5, item_status)
            
            btn_panel = QWidget()
            h_layout = QHBoxLayout(btn_panel)
            h_layout.setContentsMargins(2,2,2,2)
            
            btn_lock = QPushButton("Mở" if locked else "Khoá")
            btn_lock.clicked.connect(lambda checked, u=uid, l=locked: self.toggle_lock(u, l))
            h_layout.addWidget(btn_lock)
            
            btn_reset = QPushButton("Reset HWID")
            btn_reset.clicked.connect(lambda checked, u=uid: self.reset_devices(u))
            h_layout.addWidget(btn_reset)
            
            btn_limit = QPushButton("Sửa Giới hạn")
            btn_limit.clicked.connect(lambda checked, u=uid, l=limit: self.change_limit(u, l))
            h_layout.addWidget(btn_limit)
            
            btn_delete = QPushButton("Xoá")
            btn_delete.setStyleSheet("background-color: #dc3545; color: white;")
            btn_delete.clicked.connect(lambda checked, u=uid: self.delete_user(u))
            h_layout.addWidget(btn_delete)
            
            self.table.setCellWidget(row, 6, btn_panel)
            row += 1
            
        self.table.resizeRowsToContents()

    def create_user(self):
        email, ok1 = QInputDialog.getText(self, "Tạo User", "Nhập Email:")
        if ok1 and email:
            password, ok2 = QInputDialog.getText(self, "Tạo User", "Nhập Mật khẩu (ít nhất 6 ký tự):")
            if ok2 and password:
                success, msg = self.auth_mgr.admin_create_user(email, password)
                if success:
                    QMessageBox.information(self, "Thành công", msg)
                    self.load_users()
                else:
                    QMessageBox.warning(self, "Lỗi", msg)

    def delete_user(self, uid):
        if uid == self.auth_mgr.uid:
            QMessageBox.warning(self, "Lỗi", "Bạn không thể tự xóa tài khoản quản trị của chính mình!")
            return
            
        reply = QMessageBox.question(self, "Xác nhận", "Bạn có chắc chắn muốn xóa dữ liệu của User này khỏi Database? (Sẽ không thể đăng nhập lại tool)", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.auth_mgr.admin_delete_user(uid)
            QMessageBox.information(self, "Thành công", "Đã xóa dữ liệu trên Database!")
            self.load_users()

    def toggle_lock(self, uid, current_locked):
        self.auth_mgr.admin_update_status(uid, not current_locked)
        self.load_users()

    def reset_devices(self, uid):
        reply = QMessageBox.question(self, "Xác nhận", "Bạn có chắc muốn xoá toàn bộ HWID (thiết bị) đã lưu của user này?")
        if reply == QMessageBox.Yes:
            self.auth_mgr.admin_reset_devices(uid)
            self.load_users()

    def change_limit(self, uid, current_limit):
        limit, ok = QInputDialog.getInt(self, "Giới hạn thiết bị", "Nhập số thiết bị tối đa cho phép:", current_limit, 1, 999)
        if ok:
            self.auth_mgr.admin_update_devices_limit(uid, limit)
            self.load_users()
