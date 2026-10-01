import cv2
import numpy as np
import os

class ImageMatcher:
    def __init__(self, template_dir="templates"):
        self.template_dir = template_dir
        os.makedirs(template_dir, exist_ok=True)

    def find_image(self, screen_path, template_name, threshold=0.8):
        """
        Tìm kiếm ảnh mẫu (template_name) trong ảnh màn hình (screen_path).
        Trả về (x, y) là tọa độ trung tâm nếu tìm thấy, ngược lại trả về None.
        """
        template_path = os.path.join(self.template_dir, template_name)
        if not os.path.exists(template_path):
            print(f"Không tìm thấy file mẫu: {template_path}")
            return None
        
        if not os.path.exists(screen_path):
            print(f"Không tìm thấy file màn hình: {screen_path}")
            return None

        img = cv2.imread(screen_path)
        template = cv2.imread(template_path)
        
        if img is None or template is None:
            return None

        # Chuyển sang ảnh xám để tìm kiếm chính xác hơn và nhanh hơn
        img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

        result = cv2.matchTemplate(img_gray, template_gray, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val >= threshold:
            h, w = template_gray.shape[:2]
            center_x = max_loc[0] + w // 2
            center_y = max_loc[1] + h // 2
            return (center_x, center_y)
        
        return None
