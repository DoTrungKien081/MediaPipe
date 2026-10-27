# MemeRecognizer

Ứng dụng tương tác với webcam sử dụng **Python**, **OpenCV** và **MediaPipe**. Chương trình phân tích landmark của bàn tay và khuôn mặt, áp dụng các điều kiện hình học do dự án tự xây dựng để chọn meme tương ứng, sau đó hiển thị meme trên khung hình camera.

## Video demo

[**Xem video demo MemeRecognizer trên YouTube**](https://youtu.be/sg4XZ6K7LJ4)

## Tính năng

- Đọc hình ảnh từ webcam và xử lý theo từng khung hình.
- Sử dụng MediaPipe Face Landmarker để lấy landmark khuôn mặt và Hand Landmarker để lấy landmark bàn tay.
- Phân tích tư thế ngón tay và vị trí tương đối của bàn tay so với khuôn mặt bằng các điều kiện hình học.
- Hỗ trợ 7 meme: `SHOCKED`, `ABSOLUTE_CINEMA`, `USE_YOUR_BRAIN`, `THINKING_MONKEY`, `MONKEY_HAS_AN_IDEA`, `LIKE_CAT` và `SPEECHLESS_CAT`.
- Hiển thị meme ở góc trên bên phải khung hình. Ảnh được thay đổi kích thước về `200 × 200` pixel; ảnh có kênh alpha được hòa trộn với hình ảnh camera.

## Cấu trúc dự án

Các tệp và thư mục cần thiết khi chạy từ mã nguồn:

```text
Meme_recognizer/
├── MemeRecognizer.py
├── MemeRecognizer.spec
├── face_landmarker.task
├── hand_landmarker.task
├── MemeLib/
│   ├── AbsoluteCinema.png
│   ├── LikeCat.jpg
│   ├── MonkeyHasAnIdea.jpg
│   ├── Shocked.jpg
│   ├── SpeechlessCat.jpg
│   ├── ThinkingMonkey.jpeg
│   └── UseYourBrain.jpg
├── ReportMediaPipe.pdf
└── README.md
```

**Lưu ý:** Tên tệp, chữ hoa/chữ thường và vị trí tương đối phải được giữ chính xác. Chương trình tìm model và ảnh meme dựa trên thư mục chứa `MemeRecognizer.py` (hoặc vị trí tài nguyên của bản đóng gói). Nếu thiếu tài nguyên bắt buộc, chương trình sẽ báo lỗi. Các thư mục `env/`, `build/`, `dist/` và `__pycache__/` là thư mục môi trường hoặc sản phẩm sinh ra trong quá trình chạy/đóng gói; chúng không thay thế các tài nguyên gốc nêu trên.

## Cách 1: Chạy từ mã nguồn

### Yêu cầu

- Python 3 có phiên bản tương thích với bản MediaPipe được cài đặt.
- Webcam hoạt động.
- Môi trường đồ họa có thể mở cửa sổ OpenCV.
- Hai tệp model `face_landmarker.task`, `hand_landmarker.task` và thư mục `MemeLib/` đặt đúng vị trí như cấu trúc trên.

### Cài đặt và chạy trên Linux

Mở terminal tại thư mục gốc của repository và chạy:

```bash
python3 -m venv env
source env/bin/activate
python -m pip install --upgrade pip
python -m pip install mediapipe opencv-contrib-python
python MemeRecognizer.py
```

Lệnh tạo môi trường `env` chỉ cần chạy lần đầu. Những lần chạy sau, mở terminal tại thư mục dự án, kích hoạt môi trường rồi chạy chương trình:

```bash
source env/bin/activate
python MemeRecognizer.py
```

Chương trình mặc định mở camera có chỉ số `0`. Đóng cửa sổ **Meme Recognizer App** để kết thúc ứng dụng.

### Cài đặt và chạy trên Windows (PowerShell)

```powershell
py -3 -m venv env
.\env\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install mediapipe opencv-contrib-python
python MemeRecognizer.py
```

Nếu PowerShell chặn việc kích hoạt môi trường ảo, hãy dùng terminal phù hợp hoặc điều chỉnh chính sách thực thi theo cấu hình máy của bạn. Cần giữ các model và thư mục `MemeLib/` cạnh `MemeRecognizer.py` như phần cấu trúc dự án.

### Ghi chú cho Linux

Chương trình có tính năng hỗ trợ tự phóng to cửa sổ bằng `xdotool` và thư viện X11. Đây là tính năng tùy chọn, không cần thiết cho việc nhận diện meme. Nếu môi trường đồ họa không tương thích với X11 và việc phóng to cửa sổ gây lỗi, hãy chạy mà không có `xdotool` trong `PATH` hoặc điều chỉnh phần `maximizeWindow()` trong mã nguồn.

## Cách 2: Chạy bản thực thi đã đóng gói

Nếu chỉ muốn sử dụng ứng dụng, nên tải bản phát hành đã đóng gói dành riêng cho hệ điều hành của mình.

- Người dùng **không cần tự cài Python, MediaPipe, OpenCV hay PyInstaller** khi sử dụng bản đóng gói hoàn chỉnh.
- Dùng bản thực thi dành cho đúng hệ điều hành. Bản build Linux không mặc nhiên chạy được trên Windows hoặc macOS.
- Giữ nguyên các tài nguyên được phát hành cùng ứng dụng, gồm `face_landmarker.task`, `hand_landmarker.task` và thư mục `MemeLib/` nếu chúng nằm ngoài file thực thi. Không đổi tên hoặc di chuyển các tài nguyên này.
- Cần có webcam và môi trường đồ họa để mở cửa sổ ứng dụng.
- `xdotool` chỉ phục vụ tính năng tự phóng to cửa sổ trên môi trường Linux tương thích; không phải yêu cầu chung để chạy ứng dụng.

Nếu bản phát hành có thư mục `dist/`, hãy chạy file thực thi được tạo bên trong đó và giữ nguyên cấu trúc tài nguyên đi kèm. Tên file thực thi có thể khác nhau tùy cấu hình đóng gói.

## Đóng gói bản chạy sẵn (dành cho người phát triển)

PyInstaller chỉ cần khi tạo bản thực thi, không cần thiết khi chạy trực tiếp từ source code.

Sau khi đã cài các thư viện cần thiết trong môi trường ảo, cài PyInstaller và chạy file cấu hình đóng gói:

```bash
python -m pip install pyinstaller
pyinstaller MemeRecognizer.spec
```

Kết quả thường được đặt trong `dist/`; thư mục `build/` chứa các tệp trung gian. Hãy kiểm tra bản build thực tế để chắc chắn các model và ảnh meme được đóng gói hoặc phân phối kèm trước khi gửi cho người khác.

## Cách hoạt động

1. OpenCV đọc khung hình từ webcam, lật ngang ảnh và chuyển màu từ BGR sang RGB.
2. MediaPipe Face Landmarker và Hand Landmarker trích xuất landmark từ khung hình.
3. `identifyMeme()` tính khoảng cách giữa các landmark, đánh giá trạng thái duỗi của ngón tay và áp dụng các điều kiện nhận diện được thiết lập trong chương trình.
4. Chương trình chọn ảnh meme tương ứng và ghép ảnh lên khung hình camera bằng `overlayMeme()`.
5. Cửa sổ kết quả được cập nhật liên tục cho đến khi webcam không đọc được khung hình hoặc người dùng đóng cửa sổ.

Các meme được chọn bằng điều kiện hình học và ngưỡng thiết lập thủ công; đây không phải là một mô hình học máy được huấn luyện riêng để phân loại từng meme.

## Xử lý sự cố

- **Báo thiếu model hoặc ảnh meme:** Kiểm tra tên và vị trí của `face_landmarker.task`, `hand_landmarker.task` và các tệp trong `MemeLib/`.
- **Không mở được camera:** Kiểm tra quyền truy cập webcam, đóng các ứng dụng khác đang sử dụng camera và xác nhận camera mặc định là thiết bị `0`. Nếu cần, sửa `cv2.VideoCapture(0)` trong `MemeRecognizer.py`.
- **Không tìm thấy module `mediapipe` hoặc `cv2`:** Kích hoạt đúng môi trường ảo rồi chạy lại lệnh cài đặt thư viện ở phần hướng dẫn.
- **Lỗi tự phóng to cửa sổ trên Linux:** Kiểm tra môi trường X11/Wayland và `xdotool`. Tính năng tự phóng to không ảnh hưởng đến thuật toán nhận diện chính.

## Báo cáo

Báo cáo của dự án nằm trong [`ReportMediaPipe.pdf`](ReportMediaPipe.pdf).

## Tài liệu tham khảo

- [MediaPipe Face Landmarker](https://ai.google.dev/edge/api/mediapipe/python/mp/tasks/vision/FaceLandmarker)
- [MediaPipe Hand Landmarker](https://ai.google.dev/edge/api/mediapipe/python/mp/tasks/vision/HandLandmarker)
- [OpenCV-Python Tutorials](https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html)
