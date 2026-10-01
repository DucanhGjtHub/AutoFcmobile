import sys
import os

# Đảm bảo đường dẫn core hoạt động
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QComboBox, QFileDialog, QMessageBox, QScrollArea)
from PyQt5.QtGui import QPixmap, QPainter, QPen, QColor
from PyQt5.QtCore import Qt, QRect, QPoint
from core.adb_manager import ADBManager

class ImageCropperWidget(QLabel):
    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.drawing = False
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.pixmap_orig = None
        self.crop_rect = None

    def set_image(self, img_path):
        self.pixmap_orig = QPixmap(img_path)
        self.setPixmap(self.pixmap_orig)
        self.crop_rect = None
        self.start_point = QPoint()
        self.end_point = QPoint()

    def mousePressEvent(self, event):
        if self.pixmap_orig is None: return
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.start_point = event.pos()
            self.end_point = self.start_point
            self.update_display()

    def mouseMoveEvent(self, event):
        if self.drawing:
            self.end_point = event.pos()
            self.update_display()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.drawing:
            self.drawing = False
            self.end_point = event.pos()
            self.crop_rect = QRect(self.start_point, self.end_point).normalized()
            self.update_display()

    def update_display(self):
        if self.pixmap_orig is None: return
        temp_pixmap = self.pixmap_orig.copy()
        painter = QPainter(temp_pixmap)
        pen = QPen(QColor(255, 0, 0), 2, Qt.SolidLine)
        painter.setPen(pen)
        
        rect = QRect(self.start_point, self.end_point).normalized()
        painter.drawRect(rect)
        
        # Bôi mờ phần ngoài để dễ nhìn
        painter.fillRect(0, 0, temp_pixmap.width(), rect.top(), QColor(0, 0, 0, 100))
        painter.fillRect(0, rect.bottom(), temp_pixmap.width(), temp_pixmap.height() - rect.bottom(), QColor(0, 0, 0, 100))
        painter.fillRect(0, rect.top(), rect.left(), rect.height(), QColor(0, 0, 0, 100))
        painter.fillRect(rect.right(), rect.top(), temp_pixmap.width() - rect.right(), rect.height(), QColor(0, 0, 0, 100))
        
        painter.end()
        self.setPixmap(temp_pixmap)

    def get_cropped_image(self):
        if self.pixmap_orig and self.crop_rect and self.crop_rect.isValid():
            bounds = self.pixmap_orig.rect()
            intersected = self.crop_rect.intersected(bounds)
            if intersected.isValid() and intersected.width() > 0 and intersected.height() > 0:
                return self.pixmap_orig.copy(intersected)
        return None

class CropperMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Công Cụ Cắt Ảnh Tài Nguyên Giả Lập")
        self.resize(1000, 700)
        self.adb = ADBManager()
        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Header Controls
        control_layout = QHBoxLayout()
        
        self.btn_refresh = QPushButton("Quét thiết bị")
        self.btn_refresh.setFixedWidth(100)
        self.btn_refresh.clicked.connect(self.refresh_devices)
        
        self.combo_devices = QComboBox()
        self.combo_devices.setEditable(True)
        self.combo_devices.setFixedWidth(200)
        
        self.btn_capture = QPushButton("Chụp màn hình")
        self.btn_capture.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        self.btn_capture.clicked.connect(self.capture_screen)
        
        self.btn_save = QPushButton("Lưu vùng khoanh đỏ")
        self.btn_save.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.btn_save.clicked.connect(self.save_image)
        
        control_layout.addWidget(self.btn_refresh)
        control_layout.addWidget(QLabel("Thiết bị:"))
        control_layout.addWidget(self.combo_devices)
        control_layout.addWidget(self.btn_capture)
        control_layout.addWidget(self.btn_save)
        control_layout.addStretch()
        
        layout.addLayout(control_layout)
        
        # Scroll Area for Image
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.image_label = ImageCropperWidget()
        self.scroll_area.setWidget(self.image_label)
        layout.addWidget(self.scroll_area)
        
        self.refresh_devices()

    def refresh_devices(self):
        devices = self.adb.get_devices()
        self.combo_devices.clear()
        self.combo_devices.addItems(devices)
        if not devices:
            self.combo_devices.setCurrentText("emulator-5554")
        else:
            self.combo_devices.setCurrentIndex(0)

    def capture_screen(self):
        device_id = self.combo_devices.currentText().strip()
        if not device_id:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập ID thiết bị")
            return
            
        screen_path = "temp_capture.png"
        self.adb.screencap(device_id, screen_path)
        if os.path.exists(screen_path):
            self.image_label.set_image(screen_path)
        else:
            QMessageBox.warning(self, "Lỗi", "Không thể chụp màn hình! Vui lòng kiểm tra lại ID thiết bị.")

    def save_image(self):
        cropped = self.image_label.get_cropped_image()
        if cropped is None:
            QMessageBox.warning(self, "Lỗi", "Vui lòng dùng chuột khoanh một vùng đỏ trên ảnh trước khi lưu!")
            return
            
        # Tìm thư mục assets/autologin
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(os.path.dirname(sys.executable))
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
        default_dir = os.path.join(base_dir, "assets", "autologin")
        os.makedirs(default_dir, exist_ok=True)
        
        file_path, _ = QFileDialog.getSaveFileName(self, "Lưu ảnh tài nguyên", os.path.join(default_dir, "b1.png"), "Images (*.png)")
        if file_path:
            cropped.save(file_path)
            QMessageBox.information(self, "Thành công", f"Đã lưu ảnh vào:\n{file_path}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CropperMainWindow()
    window.show()
    sys.exit(app.exec_())
