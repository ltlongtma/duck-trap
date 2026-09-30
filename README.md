# 🦆 Duck Trap

Bẫy tóm những kẻ hay đi **"duck" máy** người khác (rời máy quên khoá → bị người
khác vào nhắn "duck" lên channel).

Ý tưởng: mày rời máy, bật Duck Trap. Màn hình trông **y như desktop đang mở
bình thường** (thực chất là ảnh mồi full màn hình). Ngay khi có kẻ **bấm phím
hoặc chạm touchpad/chuột**, chương trình sẽ **âm thầm**:

1. 📸 Chụp một tấm ảnh thủ phạm bằng webcam.
2. 🔒 Khoá máy ngay lập tức.

**Không** báo hiệu, **không** đổi màn hình, **không** tiếng động — thủ phạm chỉ
thấy máy "tự khoá" như bình thường, không biết là đã bị chụp. Ảnh lưu **chỉ ở
máy mày** trong thư mục `DuckTrap/captures`.

Hỗ trợ **macOS** và **Windows**.

---

## Cách 1 — Dùng file chạy sẵn (cho người non-tech, khỏi cài Python)

1. Vào tab **Actions** của repo trên GitHub → chọn **Build Duck Trap** →
   **Run workflow**. Đợi vài phút cho nó build xong.
   *(Hoặc nếu có bản Release thì vào mục **Releases** tải trực tiếp.)*
2. Tải file về:
   - **Windows**: `DuckTrap-Windows` → giải nén ra `DuckTrap.exe`
   - **macOS**: `DuckTrap-macOS` → giải nén ra `DuckTrap.app`
3. *(Tuỳ chọn)* Bỏ một ảnh tên **`trap.png`** vào **cùng thư mục** với
   `DuckTrap.exe` / `DuckTrap.app` — đó sẽ là ảnh mồi hiện full màn hình.
   Không có thì nó tự chụp desktop hoặc vẽ desktop giả.
4. **Double-click để chạy.** Sau vài giây là bẫy vũ trang âm thầm.
   - Lần đầu, máy sẽ hỏi quyền **Camera** → bấm **Allow / Cho phép**.
   - Windows SmartScreen có thể cảnh báo "app lạ" → *More info → Run anyway*.

> Gợi ý ảnh mồi: chụp màn hình desktop của mày (macOS `⌘⇧3`, Windows `Win+Shift+S`)
> rồi đổi tên thành `trap.png` đặt cạnh app cho giống thật.

---

## Cách 2 — Chạy từ mã nguồn (cho dev)

### macOS

```bash
./run.sh
```

Lần đầu script tự tạo virtualenv + cài dependency rồi chạy. Nó tự tìm bản
Python có **Tk ≥ 8.6** (Tk 8.5 cũ của macOS không fullscreen được) và dựng lại
venv nếu cần.

### Windows

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m duck_trap
```

### Chạy thử an toàn (không khoá máy)

```bash
python -m duck_trap --no-lock --open-folder --image duong_dan_anh.png
```

Gõ 1 phím để "sập bẫy giả", kiểm tra ảnh trong thư mục mở ra. Ưng rồi thì bỏ
`--no-lock` để dùng thật.

---

## Quyền cần cấp

Duck Trap phát hiện chạm bằng **event của Tkinter** trên cửa sổ fullscreen đang
giữ focus, nên **chỉ cần đúng 1 quyền bắt buộc: Camera**.

- **macOS**: System Settings → Privacy & Security → **Camera** → bật cho app
  (Terminal/iTerm nếu chạy mã nguồn, hoặc DuckTrap nếu chạy bản đóng gói).
- **Windows**: Settings → Privacy → **Camera** → cho phép app dùng camera.

Các quyền dưới đây **không bắt buộc**, chỉ khi dùng thêm:

- **Accessibility + Input Monitoring** (macOS) — chỉ khi chạy `--global-hook`.
- **Screen Recording** (macOS) — chỉ khi muốn ảnh mồi = tự chụp desktop. Không
  cấp thì màn hình mồi sẽ xám — khi đó dùng `--image` / bỏ `trap.png` cạnh app.

---

## Tuỳ chọn dòng lệnh

```bash
python -m duck_trap [tuỳ chọn]
```

| Tuỳ chọn                             | Ý nghĩa                                                     |
|--------------------------------------|-------------------------------------------------------------|
| `--image <đường dẫn>`                | **Ảnh mồi tự chọn** hiện full màn hình (PNG/JPG).           |
| `--camera-name "MacBook Pro Camera"` | Chọn camera **theo tên** (tránh vớ nhầm iPhone — macOS).    |
| `--list-cameras`                     | Liệt kê tên các camera rồi thoát.                           |
| `--camera 1`                         | Chọn webcam theo index (dùng khi không có `--camera-name`). |
| `--sensitivity 3`                    | Ngưỡng di chuột (pixel) tính là bị chạm. Nhỏ hơn = nhạy hơn. |
| `--arm-delay 6`                      | Giây ân hạn im lặng trước khi vũ trang (mặc định 4).        |
| `--global-hook`                      | Bắt input toàn cục (pynput). Cần Accessibility + Input Monitoring. |
| `--sound`                            | Phát tiếng khi sập bẫy (mặc định **im lặng**).             |
| `--no-lock`                          | Chỉ chụp ảnh, **không** khoá máy (dùng để test).            |
| `--open-folder`                      | Tự mở thư mục ảnh sau khi sập bẫy.                          |
| `--dir <đường dẫn>`                  | Đổi thư mục lưu ảnh.                                        |

### Chọn đúng camera (macOS — tránh camera iPhone)

macOS hay tự lấy **Continuity Camera** (iPhone). Liệt kê rồi chọn cam laptop:

```bash
./run.sh --list-cameras
./run.sh --camera-name "MacBook Pro Camera"
```

(Cần `brew install imagesnap` để chọn theo tên.)

---

## Tự đóng gói (nếu muốn build tay)

```bash
pip install pyinstaller
pyinstaller packaging/DuckTrap.spec --noconfirm
```

Hoặc dùng script có sẵn: `packaging/build_windows.bat` (Windows) /
`packaging/build_macos.sh` (macOS). Kết quả nằm ở `dist/`.

---

## Cách hoạt động (kỹ thuật)

- **Màn hình mồi**: ưu tiên ảnh mày đưa (`--image` hoặc `trap.png`), rồi tới
  screenshot desktop, cuối cùng vẽ desktop giả. Hiển thị full màn hình qua Tkinter.
- **Phát hiện chạm**: bind sự kiện `<Key>` / `<Button>` / `<Motion>` của Tkinter
  trên cửa sổ fullscreen (không cần quyền đặc biệt). Tuỳ chọn `--global-hook`
  dùng `pynput` để bắt cả khi mất focus.
- **Chụp ảnh**: `opencv-python`, hoặc `imagesnap` theo tên camera (macOS). Chụp
  **trước** khi khoá máy.
- **Khoá máy âm thầm**: macOS `CGSession -suspend` (fallback AppleScript);
  Windows `LockWorkStation`.

---

## Lưu ý

- Đây là công cụ vui trong nội bộ team, chạy trên **máy của chính mày** để
  chống bị nghịch. Ảnh chỉ nằm ở máy mày, **không gửi đi đâu cả**.
