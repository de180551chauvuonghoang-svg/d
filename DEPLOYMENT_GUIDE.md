# HƯỚNG DẪN DEPLOY TOÀN BỘ HỆ THỐNG BOT TRADE VÀNG & MT5 CHẠY 24/24 MIỄN PHÍ

Tài liệu này hướng dẫn chi tiết từng bước cách triển khai toàn bộ dự án (gồm **MetaTrader 5 + Python Backend + TypeScript Dashboard**) để bot tự động chạy 24/24 trên mây (Cloud) và bạn có thể theo dõi, điều khiển từ điện thoại ở bất kỳ đâu hoàn toàn miễn phí.

---

## 1. TỔNG QUAN KIẾN TRÚC TRIỂN KHAI

Hệ thống của chúng ta gồm 3 mắt xích liên kết chặt chẽ:
```
                      ┌──────────────────────────────────────────────┐
                      │    MÁY CHỦ CLOUD WINDOWS (VPS) CHẠY 24/24    │
                      │                                              │
                      │  ┌────────────────────────────────────────┐  │
                      │  │   MetaTrader 5 Desktop (terminal64)    │  │
                      │  │   Tài khoản: Demo #113569040           │  │
                      │  └───────────────────▲────────────────────┘  │
                      │                      │ mt5 IPC bridge        │
                      │  ┌───────────────────▼────────────────────┐  │
                      │  │   Backend Python FastAPI (Cổng 8000)   │  │
                      │  │   - AI Ensemble Gatekeeper             │  │
                      │  │   - 4 Động cơ Chiến thuật Scalper      │  │
                      │  │   - WebSocket Server (/ws)             │  │
                      │  └───────────────────▲────────────────────┘  │
                      │                      │ HTTP / WebSocket      │
                      │  ┌───────────────────▼────────────────────┐  │
                      │  │   Frontend TypeScript Dashboard (UI)   │  │
                      │  │   (Tích hợp sẵn hoặc đưa lên Vercel)   │  │
                      │  └────────────────────────────────────────┘  │
                      └──────────────────────▲───────────────────────┘
                                             │ Truy cập qua Internet
                      ┌──────────────────────┴───────────────────────┐
                      │  ĐIỆN THOẠI (iOS / Android) HOẶC LAPTOP CÁ NHÂN │
                      │  (Theo dõi PnL, nến live, nút Bật/Tắt bot)   │
                      └──────────────────────────────────────────────┘
```

> [!IMPORTANT]
> **Điểm cốt lõi:** Thư viện Python `MetaTrader5` bắt buộc phải chạy trên cùng một máy với phần mềm MT5 (`terminal64.exe`). Do đó, **MT5 và Backend Python phải được đặt cùng nhau trên một môi trường Windows**.

---

## 2. LỰA CHỌN 1 (KHUYÊN DÙNG NHẤT): CLOUD VPS WINDOWS MIỄN PHÍ (AWS / AZURE)

Đây là giải pháp chuyên nghiệp nhất: Bot và MT5 chạy hoàn toàn trên máy chủ đám mây của Amazon hoặc Microsoft, không tốn điện nhà bạn, mạng siêu tốc độ thấp ping tới sàn.

### Bước 1: Đăng ký VPS Windows Miễn Phí
- **Cách A - AWS Free Tier (Miễn phí 1 năm)**:
  1. Đăng ký tài khoản tại [aws.amazon.com](https://aws.amazon.com) (chọn gói Free Tier).
  2. Vào bảng điều khiển **EC2** $\rightarrow$ Chọn **Launch Instance**.
  3. Chọn hệ điều hành: **Microsoft Windows Server 2022 Base**.
  4. Chọn loại máy: **t2.micro** (gói có nhãn *Free tier eligible* - miễn phí 750 giờ/tháng suốt 12 tháng).
  5. Tạo Key Pair để lấy mật khẩu đăng nhập Remote Desktop (RDP).
- **Cách B - Microsoft Azure (Tặng $200 USD miễn phí)**:
  1. Đăng ký tại [azure.microsoft.com](https://azure.microsoft.com/free/).
  2. Tạo 1 máy ảo Windows Server cấu hình 2 vCPU / 4GB RAM (chạy cực mượt).

### Bước 2: Đăng nhập vào VPS và cài đặt môi trường
1. Trên máy tính của bạn, mở công cụ **Remote Desktop Connection** (có sẵn trên Windows).
2. Nhập địa chỉ IP công khai của VPS và mật khẩu để vào màn hình desktop của VPS.
3. Trên VPS, tải và cài đặt:
   - **Python 3.12**: Tải tại [python.org](https://www.python.org/downloads/) (nhớ tích chọn ô *Add Python to PATH* khi cài).
   - **MetaTrader 5**: Cài đặt phần mềm MT5 và đăng nhập tài khoản Demo của bạn (`113569040`, Server: `MetaQuotes-Demo`).
   - **Git**: Tải tại [git-scm.com](https://git-scm.com/).

### Bước 3: Tải mã nguồn dự án lên VPS
Mở PowerShell trên VPS và chạy:
```powershell
git clone https://github.com/de180551chauvuonghoang-svg/d.git
cd d
git checkout v2
python -m pip install -r requirements.txt
```

### Bước 4: Mở Port 8000 trên VPS
Để điện thoại từ bên ngoài có thể truy cập vào Dashboard:
1. **Trong Windows Firewall của VPS**:
   - Mở *Windows Defender Firewall with Advanced Security* $\rightarrow$ *Inbound Rules* $\rightarrow$ *New Rule*.
   - Chọn *Port* $\rightarrow$ *TCP* $\rightarrow$ Điền `8000` $\rightarrow$ Chọn *Allow the connection*.
2. **Trong Security Group (trên web AWS/Azure)**:
   - Thêm Inbound Rule cho cổng `8000` (Type: Custom TCP, Port Range: 8000, Source: 0.0.0.0/0).

### Bước 5: Kích hoạt hệ thống
Chỉ cần chạy:
```powershell
python run.py
```
Hệ thống sẽ bật MT5, nạp AI, kết nối WebSocket và khởi chạy máy chủ.
Bây giờ, từ điện thoại hoặc bất kỳ máy tính nào, bạn chỉ cần mở trình duyệt và gõ:
```
http://IP_CỦA_VPS:8000
```
Bạn sẽ thấy toàn bộ Dashboard TypeScript thời gian thực nhảy số và điều khiển được bot!

---

## 3. LỰA CHỌN 2 (0 ĐỒNG, NHANH NHẤT TRONG 2 PHÚT): CLOUDFLARE TUNNEL

Nếu bạn muốn chạy bot trên máy tính bàn hoặc laptop ở nhà mà vẫn muốn theo dõi, điều khiển từ điện thoại khi đi ra ngoài:

1. Tải công cụ **Cloudflare Tunnel (`cloudflared`)**:
   - Tải file thực thi `cloudflared-windows-amd64.exe` từ [github.com/cloudflare/cloudflared/releases](https://github.com/cloudflare/cloudflared/releases).
2. Chạy bot trên máy bạn bằng lệnh quen thuộc:
   ```powershell
   python run.py
   ```
3. Mở một cửa sổ PowerShell mới và gõ lệnh:
   ```powershell
   .\cloudflared.exe tunnel --url http://127.0.0.1:8000
   ```
4. Cloudflare sẽ tạo cho bạn một đường link HTTPS miễn phí có dạng:
   ```
   https://random-subdomain.trycloudflare.com
   ```
5. Bạn gửi đường link này vào điện thoại: **Bất cứ lúc nào bạn mở link đó trên điện thoại, bạn đều xem được nến nhảy, PnL real-time và có nút bấm bật/tắt bot từ xa** mà không cần mở port modem, hoàn toàn bảo mật và miễn phí 100%!

---

## 4. LỰA CHỌN 3: TÁCH FRONTEND TYPESCRIPT LÊN VERCEL

Nếu bạn muốn giao diện Dashboard được host trên nền tảng đám mây toàn cầu Vercel:

1. Đăng ký tài khoản miễn phí tại [vercel.com](https://vercel.com).
2. Chọn **Add New Project** $\rightarrow$ Kết nối với repository GitHub của bạn: `de180551chauvuonghoang-svg/d`.
3. Cấu hình triển khai:
   - **Root Directory**: Chọn thư mục `dashboard`.
   - **Framework Preset**: Chọn `Vite`.
4. Trong mục **Environment Variables**, thêm 2 biến:
   - `VITE_API_URL`: Điền địa chỉ IP của VPS (hoặc link Cloudflare Tunnel), ví dụ: `http://103.xx.xx.xx:8000`
   - `VITE_WS_URL`: Điền link WebSocket tương ứng, ví dụ: `ws://103.xx.xx.xx:8000/ws`
5. Nhấn **Deploy**.
Vercel sẽ cấp cho bạn tên miền miễn phí cực nhanh: `https://ten-du-an.vercel.app`.

---

## 5. THIẾT LẬP BOT TỰ ĐỘNG KHỞI ĐỘNG KHI VPS KHỞI ĐỘNG LẠI (AUTO-REBOOT)

Khi chạy trên máy chủ VPS, đôi khi VPS tự update Windows và khởi động lại. Để bot tự động chạy lại mà không cần bạn đăng nhập:

1. Nhấn phím `Windows + R`, gõ `shell:startup` và nhấn Enter.
2. Tạo một shortcut của file `START.bat` đặt vào thư mục Startup này.
3. Mỗi khi VPS khởi động lại, Windows sẽ tự động mở `START.bat`, khởi động MT5 và kích hoạt Bot chạy tiếp tục 24/24.
