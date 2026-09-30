# 🦆 Duck Trap

Bẫy tóm những kẻ hay đi **"duck" máy** người khác (rời máy quên khoá → bị người
khác vào nhắn "duck" lên channel).

Ý tưởng: mày rời máy, bật Duck Trap. Màn hình trông **y như desktop đang mở
bình thường** (thực chất là ảnh mồi full màn hình). Ngay khi có kẻ **bấm phím
hoặc chạm touchpad/chuột**, chương trình sẽ:

1. 📸 **Chụp một tấm ảnh** thủ phạm bằng webcam.
2. 🔴 Chớp màn hình đỏ **"GOTCHA!"**.
3. 🔒 **Tự khoá máy** ngay lập tức.

Ảnh được lưu **chỉ ở máy mày** trong `~/DuckTrap/captures/`.

---

## Cài & chạy (macOS)

Cách nhanh nhất:

```bash
./run.sh
```

Lần đầu script sẽ tự tạo virtualenv và cài dependency, rồi chạy luôn.

Hoặc thủ công:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m duck_trap
```

Sau khi chạy, có **4 giây đếm ngược** để mày rời tay khỏi bàn phím/touchpad
(nhấn **ESC** trong lúc này nếu muốn huỷ). Hết đếm ngược là bẫy vũ trang.

> Nếu không cài được `opencv-python`, dùng bản chụp ảnh của macOS:
> `brew install imagesnap` — Duck Trap sẽ tự fallback sang nó.

---

## Quyền cần cấp trên macOS (quan trọng)

macOS chặn theo dõi bàn phím và camera cho tới khi mày cấp quyền. Mở
**System Settings → Privacy & Security** và cấp cho ứng dụng chạy Python
(thường là **Terminal** hoặc **iTerm**) các quyền:

- **Camera** — để chụp ảnh thủ phạm.
- **Input Monitoring** — để bắt phím/touchpad kể cả khi cửa sổ không có focus.
- **Accessibility** — để lệnh khoá máy (AppleScript fallback) hoạt động.

Lần đầu chạy, macOS thường tự hỏi. Nếu bị từ chối nhầm, vào Settings bật lại
rồi chạy lại.

---

## Tuỳ chọn dòng lệnh

```bash
python -m duck_trap [tuỳ chọn]
```

| Tuỳ chọn            | Ý nghĩa                                                        |
|---------------------|----------------------------------------------------------------|
| `--no-lock`         | Chỉ chụp ảnh, **không** khoá máy (dùng để test cho an toàn).    |
| `--no-sound`        | Không phát tiếng khi sập bẫy.                                   |
| `--open-folder`     | Tự mở thư mục ảnh sau khi sập bẫy.                              |
| `--arm-delay 6`     | Đổi thời gian đếm ngược (giây).                                 |
| `--camera 1`        | Chọn webcam khác (nếu có nhiều camera).                         |
| `--sensitivity 3`   | Ngưỡng di chuột (pixel) tính là bị chạm. Nhỏ hơn = nhạy hơn.    |
| `--dir <đường dẫn>` | Đổi thư mục lưu ảnh.                                            |

**Khuyến nghị test lần đầu:**

```bash
python -m duck_trap --no-lock --open-folder
```

Chạy xong, tự gõ 1 phím để "sập bẫy giả", kiểm tra ảnh trong thư mục mở ra.
Khi ưng rồi thì chạy không có `--no-lock` để dùng thật.

---

## Cách hoạt động (kỹ thuật)

- **Màn hình mồi**: dùng `screencapture -x` chụp lại desktop hiện tại rồi
  hiển thị full màn hình qua Tkinter, nên trông giống hệt máy đang mở.
  Nếu không chụp được thì vẽ một desktop giả tối giản.
- **Phát hiện chạm**: dùng `pynput` lắng nghe bàn phím + chuột/touchpad ở mức
  hệ thống (nhạy kể cả khi cửa sổ không giữ focus). Không có `pynput` thì
  fallback sang sự kiện của Tkinter.
- **Chụp ảnh**: `opencv-python` (bỏ vài frame đầu cho webcam chỉnh sáng), hoặc
  fallback `imagesnap`. Ảnh được chụp **trước** khi khoá máy.
- **Khoá máy**: macOS dùng `CGSession -suspend` (về màn hình đăng nhập), có
  fallback qua AppleScript. Có sẵn nhánh cho Linux/Windows.

---

## Lưu ý

- Đây là công cụ vui trong nội bộ team, chạy trên **máy của chính mày** để
  chống bị nghịch. Nhớ báo trước với team là "máy tao có gài bẫy" cho vui vẻ,
  và chỉ dùng ảnh chụp trong phạm vi trò đùa nội bộ nhé.
- Ảnh chỉ nằm ở máy mày, không gửi đi đâu cả.
