from PyQt5.QtCore import QThread, pyqtSignal
from core.adb_manager import ADBManager
from core.image_matcher import ImageMatcher
import time
import os
import queue

class AutoLoginWorker(QThread):
    # Signals để giao tiếp với Main UI (Không chặn UI)
    log_msg = pyqtSignal(str)
    account_done = pyqtSignal(str, str) # email, status
    worker_finished = pyqtSignal(str) # device_id
    worker_update = pyqtSignal(str, str, str, str) # device_id, email, password, status

    def __init__(self, device_id, account_queue, adb_manager, image_matcher):
        super().__init__()
        self.device_id = device_id
        self.account_queue = account_queue
        self.adb = adb_manager
        self.matcher = image_matcher
        self.is_running = True

    def wait_for_image(self, target_img, screen_path, timeout=0):
        start_time = time.time()
        while self.is_running:
            if timeout > 0 and (time.time() - start_time) >= timeout:
                break
            self.adb.screencap(self.device_id, screen_path)
            pos = self.matcher.find_image(screen_path, target_img)
            if pos:
                return pos
            time.sleep(1)
        return None

    def wait_and_click(self, wait_img, screen_path, click_img=None, timeout=0):
        if timeout > 0:
            self.log_msg.emit(f"[{self.device_id}] Đang chờ {wait_img} (tối đa {timeout}s)...")
        else:
            self.log_msg.emit(f"[{self.device_id}] Đang chờ {wait_img}...")
            
        pos = self.wait_for_image(wait_img, screen_path, timeout)
        if pos:
            if click_img and click_img != wait_img:
                # Bắt buộc chờ click_img xuất hiện nếu có (cùng timeout với wait_img)
                click_pos = self.wait_for_image(click_img, screen_path, timeout)
                if click_pos:
                    self.adb.tap(self.device_id, click_pos[0], click_pos[1])
                    return True
                else:
                    self.log_msg.emit(f"[{self.device_id}] Thấy {wait_img} nhưng không thấy {click_img} để click.")
                    return False
            else:
                self.adb.tap(self.device_id, pos[0], pos[1])
                return True
        return False

    def run(self):
        self.log_msg.emit(f"[{self.device_id}] Bắt đầu luồng giả lập.")
        screen_path = f"temp_screen_{self.device_id.replace(':', '_')}.png"

        while self.is_running:
            try:
                # Lấy tài khoản từ Queue, chờ 1s để còn kiểm tra vòng lặp is_running
                account = self.account_queue.get(timeout=1)
            except queue.Empty:
                # Do not erase email/password on empty, just update status
                self.worker_update.emit(self.device_id, "KEEPLAST", "KEEPLAST", "Trống (Đã xong)")
                break # Queue trống -> Hết tài khoản -> thoát luồng
            
            email = account['email']
            password = account['password']
            
            self.log_msg.emit(f"[{self.device_id}] Đang xử lý: {email}")
            self.worker_update.emit(self.device_id, email, password, "Đang xử lý...")
            
            # KỊCH BẢN LOGIN:
            # B1: chờ start.png xuất hiện, bấm b1.png
            if not self.wait_and_click("start.png", screen_path, click_img="b1.png"):
                self.log_msg.emit(f"[{self.device_id}] Lỗi B1: Không tìm thấy start.png/b1.png")
                self.worker_update.emit(self.device_id, email, password, "Lỗi B1")
                self.account_done.emit(email, "Failed B1")
                self.account_queue.task_done()
                continue
            time.sleep(0.5)
            
            # B2: chờ b2.png, bấm b2.png
            if not self.wait_and_click("b2.png", screen_path):
                self.log_msg.emit(f"[{self.device_id}] Lỗi B2: Không tìm thấy b2.png")
                self.worker_update.emit(self.device_id, email, password, "Lỗi B2")
                self.account_done.emit(email, "Failed B2")
                self.account_queue.task_done()
                continue
            time.sleep(0.5)
            
            # B3: Tìm b3.png (ô tài khoản). Nếu không thấy thì xoá tk cũ luôn (giảm timeout từ 5s xuống 1s)
            self.log_msg.emit(f"[{self.device_id}] Đang chờ b3.png (1s)...")
            pos_b3 = self.wait_for_image("b3.png", screen_path, timeout=1)
            if pos_b3:
                self.adb.tap(self.device_id, pos_b3[0], pos_b3[1])
                time.sleep(1)
            else:
                self.log_msg.emit(f"[{self.device_id}] Không thấy b3.png, tiến hành xoá tk cũ...")
            
            # LUÔN xoá trắng (phòng trường hợp có tk cũ) - xoá 50 ký tự vì email rất dài
            self.adb.clear_text(self.device_id, 50)
            time.sleep(1)
            
            # Nhập tài khoản (email)
            self.log_msg.emit(f"[{self.device_id}] Đang nhập tài khoản...")
            self.adb.input_text(self.device_id, email)
            time.sleep(0.5)
            
            # B4: chờ b4.png, bấm b4.png
            if not self.wait_and_click("b4.png", screen_path):
                self.log_msg.emit(f"[{self.device_id}] Lỗi B4: Không tìm thấy b4.png")
                self.worker_update.emit(self.device_id, email, password, "Lỗi B4")
                self.account_done.emit(email, "Failed B4")
                self.account_queue.task_done()
                continue
            time.sleep(0.5)
            
            # LUÔN xoá trắng mật khẩu cũ (nếu có)
            self.adb.clear_text(self.device_id, 50)
            time.sleep(1)
            
            # Nhập mật khẩu
            self.log_msg.emit(f"[{self.device_id}] Đang nhập mật khẩu...")
            self.adb.input_text(self.device_id, password)
            time.sleep(0.5)
            
            # B5: chờ b5.png, bấm b5.png
            if not self.wait_and_click("b5.png", screen_path):
                self.log_msg.emit(f"[{self.device_id}] Lỗi B5: Không tìm thấy b5.png")
                self.worker_update.emit(self.device_id, email, password, "Lỗi B5")
                self.account_done.emit(email, "Failed B5")
                self.account_queue.task_done()
                continue
            
            # KIỂM TRA LỖI SAU KHI ĐĂNG NHẬP
            login_success = False
            while self.is_running:
                error_found = False
                # Quét trong vòng 5 giây xem có hiện lỗi không
                for _ in range(5):
                    time.sleep(1)
                    self.adb.screencap(self.device_id, screen_path)
                    if self.matcher.find_image(screen_path, "notconect.png") or self.matcher.find_image(screen_path, "saimk.png"):
                        error_found = True
                        break
                
                if not error_found:
                    login_success = True
                    break
                    
                # Nếu thấy lỗi, đợi 10s rồi thử lại
                self.log_msg.emit(f"[{self.device_id}] Lỗi đăng nhập -> Đợi 10s thử lại...")
                self.worker_update.emit(self.device_id, email, password, "Lỗi -> Thử lại")
                time.sleep(10)
                
                # Bấm lại B4 (ô nhập mật khẩu)
                self.wait_and_click("b4.png", screen_path, timeout=3)
                time.sleep(1)
                
                # Xoá mật khẩu cũ và nhập lại
                self.adb.clear_text(self.device_id, 50)
                time.sleep(1)
                self.adb.input_text(self.device_id, password)
                time.sleep(0.5)
                
                # Bấm lại B5
                self.wait_and_click("b5.png", screen_path, timeout=3)
                
            if not self.is_running:
                self.account_queue.task_done()
                break
            
            # Đã xong 1 tài khoản
            self.worker_update.emit(self.device_id, email, password, "Login Successful")
            self.account_done.emit(email, "Success")
            self.log_msg.emit(f"[{self.device_id}] Hoàn thành nick: {email}")
            
            # Đánh dấu đã xử lý xong item này trong Queue
            self.account_queue.task_done()

        # Dọn dẹp ảnh rác
        if os.path.exists(screen_path):
            try:
                os.remove(screen_path)
            except:
                pass
                
        self.log_msg.emit(f"[{self.device_id}] Kết thúc công việc.")
        self.worker_finished.emit(self.device_id)

    def stop(self):
        self.is_running = False
