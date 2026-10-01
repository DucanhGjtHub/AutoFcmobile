import sys
import os
import traceback

# Ghi lỗi crash ra file để debug trên máy khách
def log_crash(exc_type, exc_value, exc_tb):
    crash_info = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
    try:
        log_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        log_path = os.path.join(log_dir, "crash_log.txt")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*50}\n{crash_info}\n")
    except:
        pass

sys.excepthook = log_crash

from PyQt5.QtWidgets import QApplication, QMessageBox

# Thêm thư mục hiện tại vào sys.path để import các module core và ui được
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import MainWindow
from ui.login_window import LoginWindow
from ui.admin_window import AdminWindow

def on_login_success(role, auth_mgr=None):
    global main_window, admin_window, login_window
    try:
        login_window.hide()
        if role == "admin":
            admin_window = AdminWindow(auth_mgr)
            admin_window.show()
        else:
            main_window = MainWindow()
            main_window.show()
    except Exception as e:
        QMessageBox.critical(None, "Lỗi", f"Lỗi khi mở cửa sổ chính:\n{str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    login_window = LoginWindow(on_login_success)
    login_window.show()
    
    sys.exit(app.exec_())
