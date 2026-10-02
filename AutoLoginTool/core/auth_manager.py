import requests
import json
import subprocess
import platform
import socket
import psutil
from datetime import datetime

class AuthManager:
    def __init__(self):
        self.api_key = "AIzaSyAsJ3VgdIs22_bEZIbVOSBC_vKI6bmL_5Y"
        self.db_url = "https://autofcmobile-1f224-default-rtdb.firebaseio.com"
        self.id_token = None
        
    def get_hwid(self):
        try:
            import uuid
            mac = str(uuid.getnode())
            sys_uuid = subprocess.check_output('wmic csproduct get uuid', creationflags=0x08000000).decode().split('\n')[1].strip()
            mb = subprocess.check_output('wmic baseboard get serialnumber', creationflags=0x08000000).decode().split('\n')[1].strip()
            combined = f"{sys_uuid}-{mb}-{mac}"
            import hashlib
            return hashlib.md5(combined.encode()).hexdigest()
        except:
            import uuid
            return str(uuid.getnode())

    def get_pc_specs(self):
        try:
            ram = f"{round(psutil.virtual_memory().total / (1024.0 **3))} GB"
            cpu = platform.processor()
            gpu = "Unknown"
            try:
                gpu_info = subprocess.check_output('wmic path win32_VideoController get name', creationflags=0x08000000).decode().split('\n')[1].strip()
                if gpu_info:
                    gpu = gpu_info
            except:
                pass
                
            ip = "Unknown"
            try:
                ip = requests.get('https://api.ipify.org', timeout=3).text
            except:
                pass
                
            return {
                "name": socket.gethostname(),
                "ram": ram,
                "cpu": cpu,
                "gpu": gpu,
                "ip": ip,
                "last_login": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except:
            return {
                "name": socket.gethostname(),
                "last_login": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

    def login(self, email, password):
        # 1. Login with Firebase Auth
        auth_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={self.api_key}"
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        
        try:
            res = requests.post(auth_url, json=payload)
            data = res.json()
            if "error" in data:
                err_msg = data['error'].get('message', 'Unknown Error')
                if err_msg == "INVALID_LOGIN_CREDENTIALS":
                    return False, "Sai email hoặc mật khẩu!", None
                return False, f"Lỗi đăng nhập: {err_msg}", None
                
            id_token = data['idToken']
            self.id_token = id_token
            uid = data['localId']
            
            # 2. Check Realtime DB for limits and roles
            hwid = self.get_hwid()
            user_url = f"{self.db_url}/users/{uid}.json?auth={id_token}"
            user_res = requests.get(user_url)
            
            if user_res.status_code in (401, 403):
                return False, "Lỗi quyền truy cập Database (Permission Denied). Vui lòng cập nhật Rules trên Firebase!", None
            
            user_data = user_res.json()
            if not user_data:
                user_data = {}
                
            if user_data.get("locked") == True:
                return False, "Tài khoản của bạn đã bị khóa. Vui lòng liên hệ Admin!", None
                
            role = user_data.get("role", "user")
            devices_limit = user_data.get('devices', 1) # Default limit is 1
            registered_devices = user_data.get('registered_hwids', {})
            
            # Khởi tạo data ban đầu nếu chưa có
            if 'email' not in user_data:
                requests.put(f"{self.db_url}/users/{uid}/email.json?auth={id_token}", json=email)
            if 'devices' not in user_data:
                requests.put(f"{self.db_url}/users/{uid}/devices.json?auth={id_token}", json=devices_limit)
            if 'role' not in user_data:
                # Không được phép tự ghi role nếu rule chặn, đoạn này có thể bị fail nhưng rule của admin cho phép ghi
                # Nếu là user bình thường, ghi vào đây sẽ bị fail (do rule "role": {".write": false})
                # Nên ta phải setup từ trước. Tạm thời bỏ qua nếu bị lỗi.
                pass
            
            # Bỏ qua check HWID nếu là Admin (cho tiện debug/dùng) hoặc cứ check bình thường? Cứ check bình thường.
            
            if hwid in registered_devices:
                specs = self.get_pc_specs()
                update_url = f"{self.db_url}/users/{uid}/registered_hwids/{hwid}.json?auth={id_token}"
                requests.patch(update_url, json=specs)
                return True, "Đăng nhập thành công!", role
            else:
                if len(registered_devices) < devices_limit or role == "admin":
                    specs = self.get_pc_specs()
                    update_url = f"{self.db_url}/users/{uid}/registered_hwids/{hwid}.json?auth={id_token}"
                    res_put = requests.put(update_url, json=specs)
                    
                    if res_put.status_code in (401, 403):
                        return False, "Không thể thêm thiết bị mới (Permission Denied).", None
                        
                    return True, "Đăng nhập thành công (Thiết bị mới)!", role
                else:
                    return False, f"Tài khoản đã đạt giới hạn thiết bị ({devices_limit} thiết bị).", None
                    
        except Exception as e:
            return False, f"Lỗi kết nối: {str(e)}", None

    # ========================== ADMIN FUNCTIONS ==========================
    
    def get_all_users(self):
        res = requests.get(f"{self.db_url}/users.json?auth={self.id_token}")
        print(f"DEBUG get_all_users: {res.status_code} - {res.text}")
        if res.status_code == 200:
            return res.json() or {}
        return {}

    def admin_create_user(self, email, password):
        signup_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={self.api_key}"
        res = requests.post(signup_url, json={"email": email, "password": password, "returnSecureToken": True})
        data = res.json()
        if "error" in data:
            return False, data["error"].get("message", "Error")
        
        new_uid = data["localId"]
        
        init_data = {
            "email": email,
            "role": "user",
            "devices": 1,
            "locked": False
        }
        requests.put(f"{self.db_url}/users/{new_uid}.json?auth={self.id_token}", json=init_data)
        return True, "Thêm tài khoản thành công!"

    def admin_update_status(self, uid, locked):
        requests.put(f"{self.db_url}/users/{uid}/locked.json?auth={self.id_token}", json=locked)

    def admin_reset_devices(self, uid):
        requests.delete(f"{self.db_url}/users/{uid}/registered_hwids.json?auth={self.id_token}")

    def admin_update_devices_limit(self, uid, limit):
        requests.put(f"{self.db_url}/users/{uid}/devices.json?auth={self.id_token}", json=limit)

    def admin_delete_user(self, uid):
        requests.delete(f"{self.db_url}/users/{uid}.json?auth={self.id_token}")
