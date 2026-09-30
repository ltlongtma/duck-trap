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

### Lỗi `No module named '_tkinter'`?

Một số bản Python (điển hình **Homebrew `python@3.14`**) **không kèm tkinter**.
`run.sh` sẽ tự tìm bản Python khác có sẵn tkinter và dựng lại venv. Nếu máy
không có bản nào, cài thêm:

```bash
brew install python-tk          # hoặc đúng phiên bản: brew install python-tk@3.14
```

Hoặc ép dùng Python hệ thống của macOS (thường có sẵn tkinter):

```bash
DUCKTRAP_PYTHON=/usr/bin/python3 ./run.sh
```

---

## Quyền cần cấp trên macOS (quan trọng)

Mặc định Duck Trap phát hiện chạm bằng **event của Tkinter** trên cửa sổ
fullscreen đang giữ focus, nên **chỉ cần đúng 1 quyền: Camera**.

Mở **System Settings → Privacy & Security** và cấp cho ứng dụng chạy Python
(thường là **Terminal** hoặc **iTerm**):

- **Camera** *(bắt buộc)* — để chụp ảnh thủ phạm. Lần đầu macOS sẽ tự hỏi.

Các quyền dưới đây **không bắt buộc**, chỉ cần khi dùng tính năng thêm:

- **Accessibility + Input Monitoring** — chỉ khi chạy `--global-hook` (bắt
  input cả khi cửa sổ không có focus). Không cấp thì cứ dùng mặc định.
- **Screen Recording** — chỉ khi muốn ảnh mồi = screenshot desktop tự động.
  Không cấp thì màn hình mồi sẽ xám/trống — **dùng `--image` để tự đưa ảnh mồi**
  (không cần quyền này).

Lần đầu chạy, macOS thường tự hỏi. Nếu bị từ chối nhầm, vào Settings bật lại
rồi chạy lại.

---

## Tuỳ chọn dòng lệnh

```bash
python -m duck_trap [tuỳ chọn]
```

| Tuỳ chọn                       | Ý nghĩa                                                     |
|--------------------------------|-------------------------------------------------------------|
| `--image <đường dẫn>`          | **Ảnh mồi tự chọn** hiện full màn hình (PNG/JPG).           |
| `--camera-name "FaceTime HD Camera"` | Chọn camera **theo tên** (tránh vớ nhầm iPhone).      |
| `--list-cameras`               | Liệt kê tên các camera rồi thoát.                           |
| `--global-hook`                | Bật bắt input toàn cục (pynput). Cần Accessibility + Input Monitoring. |
| `--no-lock`                    | Chỉ chụp ảnh, **không** khoá máy (dùng để test cho an toàn). |
| `--no-sound`                   | Không phát tiếng khi sập bẫy.                               |
| `--open-folder`                | Tự mở thư mục ảnh sau khi sập bẫy.                          |
| `--arm-delay 6`                | Đổi thời gian đếm ngược (giây).                             |
| `--camera 1`                   | Chọn webcam theo index (nếu không dùng `--camera-name`).    |
| `--sensitivity 3`              | Ngưỡng di chuột (pixel) tính là bị chạm. Nhỏ hơn = nhạy hơn. |
| `--dir <đường dẫn>`            | Đổi thư mục lưu ảnh.                                        |

### Dùng ảnh mồi của riêng mày

Màn hình xám / trống là do `screencapture` bị macOS chặn (thiếu quyền
**Screen Recording**). Cách chắc ăn nhất là **tự đưa ảnh mồi**:

```bash
./run.sh --image ~/Desktop/anh_man_hinh_gia.png
```

Gợi ý: chụp màn hình desktop của mày (⌘⇧3) rồi truyền file đó vào `--image`
để trông y như máy đang mở.

### Chọn đúng camera (tránh camera iPhone)

macOS hay tự lấy **Continuity Camera** (iPhone) làm camera mặc định. Liệt kê
rồi chọn camera laptop theo tên:

```bash
./run.sh --list-cameras
./run.sh --camera-name "FaceTime HD Camera"
```

(Cần `brew install imagesnap` để chọn theo tên.)

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
