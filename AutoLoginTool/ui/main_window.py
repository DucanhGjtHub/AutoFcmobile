from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QTextEdit, QLabel, QTableWidget, 
                             QTableWidgetItem, QFileDialog, QMessageBox, QGroupBox,
                             QSpinBox)
from PyQt5.QtCore import Qt
import queue
import os
import json

from core.account_manager import AccountManager
from core.adb_manager import ADBManager
from core.image_matcher import ImageMatcher
from core.worker import AutoLoginWorker

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Auto Login Tool - Đa Luồng LDPlayer")
        self.resize(1000, 700)
        
        if not os.path.exists("data"):
            os.makedirs("data")
            
        self.acc_mgr = AccountManager()
        self.adb_mgr = ADBManager()
        
        import sys
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            
        template_dir_path = os.path.join(base_dir, "assets", "autologin")
        self.img_matcher = ImageMatcher(template_dir=template_dir_path)
        
        self.workers = []
        self.acc_queue = queue.Queue()
        self.device_row_map = {}
        
        self.init_ui()
        self.load_config()
        self.update_total_label()
        
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # ---------------- PHẦN 1: CẤU HÌNH & ĐIỀU KHIỂN ----------------
        layout_top = QHBoxLayout()
        
        # Nhập nick
        group_acc = QGroupBox("Quản lý Nick")
        layout_acc = QHBoxLayout()
        self.txt_accounts = QTextEdit()
        self.txt_accounts.setPlaceholderText("Dán tk/mk vào đây (tk<tab>mk)...\nBấm Thêm từ Text")
        self.txt_accounts.setMaximumHeight(80)
        layout_acc.addWidget(self.txt_accounts)
        
        layout_btn_add = QVBoxLayout()
        btn_add_text = QPushButton("Thêm từ Text")
        btn_add_text.clicked.connect(self.add_from_text)
        layout_btn_add.addWidget(btn_add_text)
        
        btn_add_excel = QPushButton("Thêm từ Excel")
        btn_add_excel.clicked.connect(self.add_from_excel)
        layout_btn_add.addWidget(btn_add_excel)
        
        btn_clear = QPushButton("Xóa tất cả")
        btn_clear.clicked.connect(self.clear_accounts)
        layout_btn_add.addWidget(btn_clear)
        
        layout_acc.addLayout(layout_btn_add)
        group_acc.setLayout(layout_acc)
        layout_top.addWidget(group_acc, 2)
        
        # Điều khiển
        group_ctrl = QGroupBox("Điều khiển")
        layout_ctrl = QVBoxLayout()
        
        layout_batch = QHBoxLayout()
        layout_batch.addWidget(QLabel("Số tab chạy:"))
        self.spin_threads = QSpinBox()
        self.spin_threads.setRange(1, 100)
        self.spin_threads.setValue(20)
        layout_batch.addWidget(self.spin_threads)
        
        layout_batch.addWidget(QLabel("Từ acc:"))
        self.spin_from = QSpinBox()
        self.spin_from.setRange(1, 999999)
        self.spin_from.setValue(1)
        layout_batch.addWidget(self.spin_from)
        
        layout_batch.addWidget(QLabel("Đến:"))
        self.spin_to = QSpinBox()
        self.spin_to.setRange(1, 999999)
        self.spin_to.setValue(20)
        layout_batch.addWidget(self.spin_to)
        
        self.spin_threads.valueChanged.connect(self.sync_spin_to)
        self.spin_from.valueChanged.connect(self.sync_spin_to)
        
        btn_back = QPushButton("< Back")
        btn_back.clicked.connect(self.batch_back)
        layout_batch.addWidget(btn_back)
        
        btn_next = QPushButton("Next >")
        btn_next.clicked.connect(self.batch_next)
        layout_batch.addWidget(btn_next)
        
        layout_ctrl.addLayout(layout_batch)
        
        layout_run = QHBoxLayout()
        btn_connect = QPushButton("Kết nối & Quét ADB")
        btn_connect.clicked.connect(self.connect_adb)
        layout_run.addWidget(btn_connect)
        
        self.btn_start = QPushButton("BẮT ĐẦU CHẠY")
        self.btn_start.setStyleSheet("background-color: #28a745; color: white; font-weight: bold;")
        self.btn_start.clicked.connect(self.start_auto)
        layout_run.addWidget(self.btn_start)
        
        self.btn_stop = QPushButton("DỪNG LẠI")
        self.btn_stop.setStyleSheet("background-color: #dc3545; color: white; font-weight: bold;")
        self.btn_stop.clicked.connect(self.stop_auto)
        self.btn_stop.setEnabled(False)
        layout_run.addWidget(self.btn_stop)
        
        layout_ctrl.addLayout(layout_run)
        
        self.lbl_total = QLabel("Tổng số ních: 0")
        layout_ctrl.addWidget(self.lbl_total)
        
        group_ctrl.setLayout(layout_ctrl)
        layout_top.addWidget(group_ctrl, 3)
        
        main_layout.addLayout(layout_top)
        
        # ---------------- PHẦN 2: TABLE HIỂN THỊ GIẢ LẬP ----------------
        self.table_emu = QTableWidget()
        self.table_emu.setColumnCount(6)
        self.table_emu.setHorizontalHeaderLabels(["#", "Title", "Connection", "Email", "Password", "Status"])
        self.table_emu.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_emu.horizontalHeader().setStretchLastSection(True)
        main_layout.addWidget(self.table_emu, 3)
        
        # ---------------- PHẦN 3: LOG ----------------
        self.txt_log = QTextEdit()
        self.txt_log.setReadOnly(True)
        self.txt_log.setMaximumHeight(150)
        main_layout.addWidget(self.txt_log, 1)

    def load_config(self):
        config_path = "data/ui_config.json"
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.spin_threads.setValue(data.get("threads", 20))
                    self.spin_from.setValue(data.get("from_acc", 1))
                    self.spin_to.setValue(data.get("to_acc", 20))
            except:
                pass

    def save_config(self):
        config_path = "data/ui_config.json"
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump({
                    "threads": self.spin_threads.value(),
                    "from_acc": self.spin_from.value(),
                    "to_acc": self.spin_to.value()
                }, f)
        except:
            pass

    def closeEvent(self, event):
        self.save_config()
        event.accept()

    def sync_spin_to(self):
        # Đảm bảo Từ acc đến Đến acc có số lượng đúng bằng Số tab chạy
        self.spin_to.setValue(self.spin_from.value() + self.spin_threads.value() - 1)

    def batch_next(self):
        step = self.spin_threads.value()
        self.spin_from.setValue(self.spin_from.value() + step)
        self.save_config()
        
    def batch_back(self):
        step = self.spin_threads.value()
        new_from = max(1, self.spin_from.value() - step)
        self.spin_from.setValue(new_from)
        self.save_config()

    def log(self, msg):
        self.txt_log.append(msg)
        self.txt_log.verticalScrollBar().setValue(self.txt_log.verticalScrollBar().maximum())

    def update_total_label(self):
        accounts = self.acc_mgr.get_accounts()
        self.lbl_total.setText(f"Tổng số ních đã lưu: {len(accounts)}")

    def add_from_text(self):
        text = self.txt_accounts.toPlainText()
        if text:
            count = self.acc_mgr.add_from_text(text)
            self.log(f"-> Đã tải và lưu {count} tài khoản từ đoạn văn bản.")
            self.txt_accounts.clear()
            self.update_total_label()

    def add_from_excel(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Chọn file Excel", "", "Excel Files (*.xlsx *.xls)")
        if file_path:
            count = self.acc_mgr.add_from_excel(file_path)
            self.log(f"-> Đã tải và lưu {count} tài khoản từ file excel.")
            self.update_total_label()

    def clear_accounts(self):
        reply = QMessageBox.question(self, 'Xác nhận', 'Bạn có chắc muốn xóa tất cả tài khoản đã lưu?', QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.acc_mgr.clear_accounts()
            self.update_total_label()
            self.log("-> Đã xóa sạch tài khoản.")

    def scan_devices(self):
        devices = self.adb_mgr.get_devices()
        self.table_emu.setRowCount(0)
        self.device_row_map.clear()
        
        if devices:
            devices = sorted(devices)
            self.table_emu.setRowCount(len(devices))
            for i, dev in enumerate(devices):
                self.device_row_map[dev] = i
                
                dev_name = f"Emulator-{i+1}"
                if "16384" in dev or "7555" in dev:
                    dev_name = f"Mumu-{i+1}"
                elif "620" in dev:
                    dev_name = f"Nox-{i+1}"
                elif "emulator-" in dev:
                    dev_name = f"LDPlayer-{i+1}"
                    
                self.table_emu.setItem(i, 0, QTableWidgetItem(str(i+1)))
                self.table_emu.setItem(i, 1, QTableWidgetItem(dev_name))
                self.table_emu.setItem(i, 2, QTableWidgetItem("Connected"))
                self.table_emu.setItem(i, 3, QTableWidgetItem(""))
                self.table_emu.setItem(i, 4, QTableWidgetItem(""))
                self.table_emu.setItem(i, 5, QTableWidgetItem("Ready"))
            self.log(f"-> Đã quét thấy {len(devices)} thiết bị đang bật.")
        else:
            self.log("-> Không tìm thấy thiết bị nào.")
        return devices

    def connect_adb(self):
        self.adb_mgr.connect()
        self.log("-> Đã gọi lệnh khởi động ADB Server.")
        self.scan_devices()

    def start_auto(self):
        devices = self.adb_mgr.get_devices()
        if not devices:
            QMessageBox.warning(self, "Lỗi", "Không tìm thấy thiết bị nào! Hãy quét ADB.")
            return
            
        all_accs = self.acc_mgr.get_accounts()
        if not all_accs:
            QMessageBox.warning(self, "Lỗi", "Không có tài khoản nào!")
            return

        start_idx = self.spin_from.value() - 1
        end_idx = self.spin_to.value()
        
        if start_idx >= len(all_accs):
            QMessageBox.warning(self, "Lỗi", "Số thứ tự Từ acc vượt quá tổng số nick!")
            return
            
        accs_to_run = all_accs[start_idx:end_idx]

        self.acc_queue = queue.Queue()
        for acc in accs_to_run:
            self.acc_queue.put(acc)
            
        max_threads = self.spin_threads.value()
        active_devices = sorted(devices)[:max_threads]
            
        self.log(f"===== BẮT ĐẦU CHẠY =====")
        self.log(f"-> Phân bổ {len(accs_to_run)} tài khoản (từ {start_idx+1} đến {start_idx+len(accs_to_run)}) cho {len(active_devices)} tab...")
        
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.auto_stopped = False
        self.workers = []
        
        for dev in active_devices:
            worker = AutoLoginWorker(dev, self.acc_queue, self.adb_mgr, self.img_matcher)
            worker.log_msg.connect(self.log)
            worker.account_done.connect(self.on_account_done)
            worker.worker_finished.connect(self.on_worker_finished)
            worker.worker_update.connect(self.on_worker_update)
            self.workers.append(worker)
            worker.start()

    def stop_auto(self):
        self.auto_stopped = True
        self.log("-> Đang yêu cầu dừng các luồng. Vui lòng đợi các tab hoàn thành nick hiện tại...")
        for worker in self.workers:
            worker.stop()
        self.btn_stop.setEnabled(False)

    def on_account_done(self, email, status):
        self.acc_mgr.update_status(email, status)
        self.update_total_label()

    def on_worker_update(self, device_id, email, password, status):
        if device_id in self.device_row_map:
            row = self.device_row_map[device_id]
            self.table_emu.setItem(row, 3, QTableWidgetItem(email))
            self.table_emu.setItem(row, 4, QTableWidgetItem(password))
            self.table_emu.setItem(row, 5, QTableWidgetItem(status))

    def on_worker_finished(self, device_id):
        if device_id in self.device_row_map:
            row = self.device_row_map[device_id]
            self.table_emu.setItem(row, 5, QTableWidgetItem("Hoàn thành"))
            
        all_done = all(not w.isRunning() for w in self.workers)
        if all_done:
            self.log("===== TẤT CẢ CÁC LUỒNG ĐÃ DỪNG =====")
            self.btn_start.setEnabled(True)
            self.btn_stop.setEnabled(False)
            if not getattr(self, 'auto_stopped', False):
                self.batch_next()
