# HỆ THỐNG FORWARD TESTING REAL-TIME (FASTAPI BACKEND + TYPESCRIPT DASHBOARD)

Hệ thống giao dịch Vàng (XAUUSD) tự động kết nối trực tiếp **MetaTrader 5 (MT5)**, kiến trúc phân tách **Backend Python (FastAPI + WebSocket)** và **Frontend TypeScript (React Dashboard)** giúp theo dõi, kiểm soát và vận hành các lệnh chạy theo thời gian thực để chuẩn bị cho giai đoạn **Forward Test thực tế**.

---

## 1. TỔNG QUAN KIẾN TRÚC HỆ THỐNG

```
                    ┌────────────────────────────────────────┐
                    │     MetaTrader 5 Terminal (MT5)        │
                    │  Demo #113569040 - MetaQuotes-Demo     │
                    └───────────────────▲────────────────────┘
                                        │ (mt5 IPC bridge)
                                        │
                    ┌───────────────────▼────────────────────┐
                    │     PYTHON BACKEND (FastAPI Server)    │
                    │     - Cung cấp REST APIs               │
                    │     - Real-Time WebSocket (/ws)        │
                    │     - Bot AutoTrade Worker Thread      │
                    │     - 4 Động cơ Chiến thuật + Siêu AI  │
                    └───────────────────▲────────────────────┘
                                        │ (WebSocket 1000ms stream)
                                        │ (REST API actions)
                    ┌───────────────────▼────────────────────┐
                    │     TYPESCRIPT REACT DASHBOARD (UI)    │
                    │     - Glassmorphism Fintech Dark Theme │
                    │     - Real-time Balance, Equity, PnL   │
                    │     - Quản lý lệnh 3-Tier Scale-Out    │
                    │     - AI Confidence Gauge (P-Win)      │
                    │     - Nút Bật/Tắt Bot & Đóng Khẩn Cấp  │
                    └────────────────────────────────────────┘
```

---

## 2. CÁC TÍNH NĂNG CHÍNH CỦA GIAO DIỆN TYPESCRIPT (DASHBOARD)

1. **Thanh Trạng Thái & Nút Điều Khiển Master**:
   - Hiển thị kết nối trực tiếp tài khoản MT5 Demo (`#113569040`).
   - Đèn báo trạng thái thị trường Vàng (Mở cửa 24/5 vs Chế độ Chờ Cuối Tuần theo giờ Việt Nam).
   - Nút **KÍCH HOẠT / TẠM DỪNG BOT** với hiệu ứng phát sáng.
   - Nút **ĐÓNG TẤT CẢ (Emergency Close All)** khi có biến động bất ngờ.

2. **5 Thẻ Chỉ Số Tài Khoản Real-Time (KPI Cards)**:
   - **Số dư (Balance)**: Cập nhật biến động tức thì từ MT5.
   - **Tài sản (Equity)**: Tính toán theo giá thị trường hiện tại.
   - **Lợi nhuận thả nổi (Floating PnL)**: Đổi màu xanh/đỏ nhấp nháy theo từng tick giá.
   - **Ký quỹ còn dư (Free Margin)** & Tỷ lệ đòn bẩy 1:100.
   - **Giá Vàng Live Ticker (XAUUSD)**: Giá Bid, Giá Ask, và Spread thực tế (35 points = $0.35).

3. **Bảng Quản Lý Vị Thế Đang Mở (Active Positions Table)**:
   - Hiển thị chi tiết từng lệnh con: Mã vé (Ticket), Loại lệnh (BUY/SELL), Khối lượng Lot, Giá vào, Giá hiện tại, SL, TP.
   - Huy hiệu **ĐÃ KHÓA LÃI BE (Shield Badge)** tự động sáng lên khi bot kích hoạt dời Stop Loss về hòa vốn.
   - Nút đóng lệnh thủ công từng vị thế.

4. **Trí Tuệ Nhân Tạo & Đa Chiến Thuật (AI Intelligence Panel)**:
   - **Thanh đo Xác Suất Thắng AI (P-Win Gauge)**: Hiển thị độ tin cậy thời gian thực của nến M5 hiện tại so với ngưỡng duyệt lệnh &ge; 78%.
   - **Checklist 4 Động Cơ Chiến Thuật**:
     - Xu hướng dài hạn EMA 200 (Bullish / Bearish / Neutral).
     - Chỉ số RSI(7) và RSI(14).
     - Trạng thái bẫy giá SMC (Quét đỉnh / Quét đáy thanh khoản).
     - Trạng thái nén biên độ dao động (Volatility Squeeze inside Keltner Channel).

5. **Nhật Ký Thực Thi Thời Gian Thực (Live Terminal)**:
   - Dòng log trôi thời gian thực ghi nhận từng bước phân tích của AI, kiểm tra Spread, khớp lệnh và dời Stop Loss Breakeven.

---

## 3. HƯỚNG DẪN KHỞI CHẠY DỄ DÀNG (1-CLICK LAUNCH)

### Bước 1: Khởi động hệ thống (Tự động mở trình duyệt)
Mở cửa sổ dòng lệnh PowerShell trong thư mục này và gõ:
```powershell
python start_app.py
```
Hệ thống sẽ:
1. Tự động kết nối MT5 terminal `#113569040`.
2. Khởi chạy Backend FastAPI + WebSocket tại `http://127.0.0.1:8000`.
3. Tự động mở trình duyệt web hiển thị Dashboard giao diện TypeScript thời gian thực!

### Bước 2: Dành cho lập trình viên phát triển giao diện (Hot-Reload Dev Server)
Nếu bạn muốn chỉnh sửa code TypeScript trong `dashboard/src/App.tsx` và thấy thay đổi ngay lập tức:
```powershell
npm --prefix dashboard run dev
```
Trình duyệt dev server sẽ chạy tại: `http://localhost:5173`.

---

## 4. DANH SÁCH TẬP TIN HỆ THỐNG MỚI

- [backend_api.py](file:///c:/Users/RinHeo/Desktop/New%20folder%20(2)/backend_api.py): Máy chủ FastAPI, WebSocket endpoint `/ws`, REST APIs và cầu nối MT5.
- [start_app.py](file:///c:/Users/RinHeo/Desktop/New%20folder%20(2)/start_app.py): Script khởi chạy 1-click tích hợp tự động mở trình duyệt.
- `dashboard/`:
  - `src/App.tsx`: Mã nguồn giao diện chính bằng React TypeScript.
  - `src/types.ts`: Định nghĩa kiểu dữ liệu TypeScript đồng bộ với Backend.
  - `src/index.css`: Hệ thống thiết kế Glassmorphism Fintech Dark Mode.
  - `dist/`: Bản build tĩnh tối ưu hóa cao được Backend phục vụ trực tiếp.
- [run_backtest_v2.py](file:///c:/Users/RinHeo/Desktop/New%20folder%20(2)/run_backtest_v2.py): Công cụ chạy backtest độc lập Version 2.
- [verify_trade.py](file:///c:/Users/RinHeo/Desktop/New%20folder%20(2)/verify_trade.py): Công cụ kiểm chứng từng lệnh độc lập không rò rỉ tương lai.
