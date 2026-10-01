# manager.py
from device import Emulator, get_running_dv

class EmulatorManager:
    def __init__(self):
        self.emulators = {}

    # 🔥 Load và đồng bộ device
    def load_devices(self):
        devices = get_running_dv()

        # Thêm device mới
        for device_id in devices:
            if device_id not in self.emulators:
                self.emulators[device_id] = Emulator(device_id)

        # Xóa device đã offline
        for device_id in list(self.emulators.keys()):
            if device_id not in devices:
                del self.emulators[device_id]
        
        return list(self.emulators.keys())

    def get_emulator(self, device_id):
        return self.emulators.get(device_id)

    def show_all(self):
        for device_id in self.emulators:
            print(device_id)