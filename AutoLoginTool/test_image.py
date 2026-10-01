import sys
import os
import cv2

def test_matching(device_id, template_name):
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from core.adb_manager import ADBManager
    adb_mgr = ADBManager()
    
    screen_path = "test_screen.png"
    print(f"Đang chụp màn hình thiết bị {device_id}...")
    adb_mgr.screencap(device_id, screen_path)
    
    if not os.path.exists(screen_path):
        print("Lỗi: Không thể chụp màn hình.")
        return
        
    # Thử tìm file mẫu ở các đường dẫn có thể
    template_path = os.path.join("assets", "autologin", template_name)
    if not os.path.exists(template_path):
        template_path = os.path.join("..", "assets", "autologin", template_name)
        
    if not os.path.exists(template_path):
        print(f"Lỗi: Không tìm thấy ảnh mẫu (đã tìm trong thư mục assets/autologin).")
        return
        
    print(f"File màn hình: {screen_path}")
    print(f"File mẫu: {template_path}")
    
    img = cv2.imread(screen_path)
    template = cv2.imread(template_path)
    
    if img is None:
        print("Lỗi: OpenCV không đọc được ảnh màn hình.")
        return
    if template is None:
        print("Lỗi: OpenCV không đọc được ảnh mẫu.")
        return
        
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
    
    result = cv2.matchTemplate(img_gray, template_gray, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    
    print(f"\n=> ĐỘ GIỐNG CỦA ẢNH (Confidence/max_val): {max_val:.4f}")
    if max_val >= 0.8:
        print(f"=> KẾT LUẬN: THÀNH CÔNG! Độ giống >= 0.8, toạ độ tìm thấy: {max_loc}.")
    else:
        print(f"=> KẾT LUẬN: THẤT BẠI! Độ giống quá thấp (< 0.8). Do ảnh quá khác hoặc độ phân giải giả lập không đúng.")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Cách dùng: python test_image.py <tên_thiết_bị> <tên_file_ảnh>")
        print("Ví dụ: python test_image.py emulator-5554 start.png")
    else:
        test_matching(sys.argv[1], sys.argv[2])
