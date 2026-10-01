import subprocess
import os

class ADBManager:
    def __init__(self):
        # Ưu tiên dùng adb trong thư mục dự án (adb/adb.exe)
        self.adb_path = "adb"
        if os.path.exists("adb/adb.exe"):
            self.adb_path = os.path.abspath("adb/adb.exe")
        # Flag để ẩn hoàn toàn cửa sổ cmd đen khi gọi subprocess trên Windows
        self.CREATE_NO_WINDOW = 0x08000000

    def run_cmd(self, args):
        try:
            # Truyền mảng args trực tiếp thay vì shell=True giúp giảm tải CPU và mượt hơn
            result = subprocess.run([self.adb_path] + args, capture_output=True, text=True, timeout=10, creationflags=self.CREATE_NO_WINDOW)
            return result.stdout
        except Exception as e:
            print(f"ADB Error: {e}")
            return ""

    def connect(self):
        self.run_cmd(["start-server"])
        import threading
        import subprocess
        
        # Quét các cổng phổ biến
        ports = [5555 + (i * 2) for i in range(50)] # LDPlayer / BlueStacks
        ports += [62001] + [62025 + i for i in range(20)] # Nox
        ports += [7555] + [16384 + i for i in range(20)] # Mumu
        
        def connect_task(p):
            try:
                subprocess.run([self.adb_path, "connect", f"127.0.0.1:{p}"], 
                               capture_output=True, timeout=1, creationflags=self.CREATE_NO_WINDOW)
            except:
                pass
                
        threads = []
        for p in ports:
            t = threading.Thread(target=connect_task, args=(p,))
            threads.append(t)
            t.start()
            
        for t in threads:
            t.join()

    def get_devices(self):
        output = self.run_cmd(["devices"])
        devices = []
        for line in output.split('\n'):
            if '\tdevice' in line:
                device_id = line.split('\t')[0]
                devices.append(device_id)
                
        # Lọc trùng lặp giữa emulator-X và 127.0.0.1:X+1 (đặc thù LDPlayer)
        emulator_ports = []
        for dev in devices:
            if dev.startswith("emulator-"):
                try:
                    port = int(dev.split("-")[1]) + 1
                    emulator_ports.append(f"127.0.0.1:{port}")
                except:
                    pass
                    
        unique_devices = [d for d in devices if d not in emulator_ports]
        return unique_devices

    def screencap(self, device_id, save_path):
        # Dùng exec-out lấy dữ liệu raw trực tiếp lên RAM, bỏ qua bước lưu vào /sdcard/ và pull
        # Giúp tốc độ chụp nhanh gấp 10 lần, không gây khựng lag khi chạy 20 tab
        try:
            result = subprocess.run([self.adb_path, "-s", device_id, "exec-out", "screencap", "-p"], 
                                    capture_output=True, timeout=5, creationflags=self.CREATE_NO_WINDOW)
            if result.stdout and len(result.stdout) > 100:
                with open(save_path, "wb") as f:
                    f.write(result.stdout)
            else:
                # Fallback nếu giả lập cũ không hỗ trợ exec-out
                self.run_cmd(["-s", device_id, "shell", "screencap", "-p", "/sdcard/screen.png"])
                self.run_cmd(["-s", device_id, "pull", "/sdcard/screen.png", save_path])
        except Exception:
            pass

    def tap(self, device_id, x, y):
        self.run_cmd(["-s", device_id, "shell", "input", "tap", str(x), str(y)])

    def input_text(self, device_id, text):
        safe_text = text.replace(" ", "%s")
        # Bảo vệ ký tự đặc biệt bằng nháy đơn để tránh lỗi trên Android shell
        safe_text = safe_text.replace("'", "'\"'\"'")
        self.run_cmd(["-s", device_id, "shell", "input", "text", f"'{safe_text}'"])

    def clear_text(self, device_id, length=50):
        # Di chuyển con trỏ xuống cuối (KEYCODE_MOVE_END = 123)
        self.run_cmd(["-s", device_id, "shell", "input", "keyevent", "123"])
        # Nhấn nút xóa (KEYCODE_DEL = 67) nhiều lần
        dels = ["67"] * length
        self.run_cmd(["-s", device_id, "shell", "input", "keyevent"] + dels)
