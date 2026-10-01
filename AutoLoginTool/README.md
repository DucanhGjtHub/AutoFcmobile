# Auto FCMobile Tool

Công cụ tự động hóa việc đăng nhập và quản lý nhiều tab giả lập (LDPlayer, Nox, Mumu...) thông qua ADB. Tích hợp tính năng nhận dạng hình ảnh tự động qua OpenCV.

## Tính Năng Chính
- **Quản lý đa luồng (Multi-threading)**: Điều khiển hàng chục tab giả lập song song không gây giật lag.
- **Auto Login tự động**: 
  - Gõ tài khoản, mật khẩu tự động.
  - Tự động nhận diện các nút bấm trên màn hình (start, đăng nhập, ô trống) bằng thuật toán so sánh ảnh.
  - Tự động phát hiện lỗi và đăng nhập lại.
- **Công cụ Cắt Ảnh (`image_cropper.py`)**: Hỗ trợ trực tiếp chụp màn hình giả lập, khoanh vùng, và lưu ảnh nút bấm để thay thế linh hoạt cho nhiều độ phân giải khác nhau.
- **Script Test Ảnh (`test_image.py`)**: Công cụ debug giúp kiểm tra độ giống (confidence) của ảnh mẫu trên từng giả lập cụ thể.
- **Quản lý tài khoản bằng Excel**: Tự động lấy danh sách tài khoản cần xử lý từ file `.xlsx` và hiển thị trực quan tiến độ trên giao diện (PyQt5).

## Hướng Dẫn Cài Đặt (Môi Trường Dev)

1. Cài đặt Python 3.9+
2. Khởi tạo môi trường ảo (tuỳ chọn nhưng khuyến nghị):
   ```cmd
   python -m venv venv
   venv\Scripts\activate
   ```
3. Cài đặt thư viện:
   ```cmd
   pip install -r requirements.txt
   ```
4. Chạy tool chính:
   ```cmd
   python main.py
   ```

## Hướng Dẫn Chạy Công Cụ (Bản Build)

Nếu bạn mang sang máy khác không có Python, hãy chạy file `AutoLoginTool.exe` nằm trong thư mục `AutoLoginTool_dist`.
- File **run_test.bat**: Để test điểm ảnh (confidence) trên giả lập mới.
- File **Chup_Anh_Gia_Lap.bat**: Mở công cụ cắt và lưu lại ảnh (dành cho khi máy mới khác độ phân giải).

## Kiến Trúc
- **UI**: PyQt5 (`ui/main_window.py`, `ui/login_window.py`).
- **Core**: 
  - `adb_manager.py`: Quản lý kết nối ADB tối ưu.
  - `image_matcher.py`: Nhận dạng hình ảnh bằng OpenCV (`cv2.matchTemplate`).
  - `worker.py`: Các QThread để thực thi logic đăng nhập riêng biệt trên từng giả lập.

## Lưu Ý
Thư mục `assets/autologin` chứa các file ảnh mẫu (template). Nếu bạn dùng màn hình có độ phân giải khác, hãy dùng `Chup_Anh_Gia_Lap.bat` cắt lại các ảnh: `start.png`, `b1.png`, `b2.png`, `b3.png`, `b4.png`, `b5.png`.
