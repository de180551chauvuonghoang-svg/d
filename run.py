"""
================================================================================
          LỆNH CHẠY DUY NHẤT - HỆ THỐNG FORWARD TESTING AI SCALPER
================================================================================
Chỉ cần chạy lệnh:
    python run.py
hoặc click đúp chuột vào file:
    START.bat

Hệ thống sẽ TỰ ĐỘNG:
1. Kiểm tra và mở phần mềm MetaTrader 5 (MT5).
2. Kết nối tài khoản Demo $5,000 USD (Login: 113569040).
3. Tải Siêu mô hình AI Ensemble và 4 Động cơ Chiến thuật.
4. Tự động KÍCH HOẠT Bot Trade vào trạng thái Live (Quét nến & sẵn sàng khớp lệnh).
5. Khởi động Backend API + Real-Time WebSocket stream.
6. TỰ ĐỘNG BẬT TRÌNH DUYỆT hiển thị Giao diện TypeScript Dashboard tại:
   http://127.0.0.1:8000
================================================================================
"""
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import os
import time
import subprocess
import webbrowser
import threading
import uvicorn
from config import config

def ensure_mt5_running():
    """Kiểm tra xem MT5 terminal đã mở chưa, nếu chưa thì tự động bật"""
    mt5_exe = config.MT5_PATH
    if os.path.exists(mt5_exe):
        try:
            # Kiểm tra tiến trình terminal64
            tasks = subprocess.check_output('tasklist /FI "IMAGENAME eq terminal64.exe"', shell=True).decode('utf-8', errors='ignore')
            if "terminal64.exe" not in tasks:
                print(f"[MT5] Đang tự động khởi chạy MetaTrader 5 từ: {mt5_exe} ...")
                subprocess.Popen([mt5_exe])
                time.sleep(3)
            else:
                print("[MT5] Phần mềm MetaTrader 5 đã đang chạy.")
        except Exception as e:
            print(f"[Cảnh báo] Kiểm tra tiến trình MT5: {e}")
    else:
        print(f"[Cảnh báo] Không tìm thấy file MT5 tại {mt5_exe}")

def ensure_frontend_built():
    """Kiểm tra bản build của giao diện TypeScript"""
    dist_file = os.path.join(os.path.dirname(__file__), "dashboard", "dist", "index.html")
    if not os.path.exists(dist_file):
        print("[Dashboard] Đang tự động build giao diện TypeScript React...")
        subprocess.run(["npm", "--prefix", "dashboard", "run", "build"], shell=True)

def open_browser():
    """Tự động mở trình duyệt sau khi server khởi động"""
    time.sleep(1.8)
    url = "http://127.0.0.1:8000"
    print(f"\n[Trình Duyệt] Đang tự động mở Giao diện Web Dashboard tại: {url} ...\n")
    webbrowser.open(url)

def main():
    print("=" * 75)
    print("      KHỞI ĐỘNG HỆ THỐNG FORWARD TESTING REAL-TIME TOÀN DIỆN (1-CLICK)")
    print("      MetaTrader 5 (Demo #113569040) + Siêu AI Ensemble + TypeScript Dashboard")
    print("=" * 75)
    
    # 1. Tự động kiểm tra và mở MT5
    ensure_mt5_running()
    
    # 2. Đảm bảo giao diện đã build
    ensure_frontend_built()
    
    # 3. Lên lịch tự động bật trình duyệt
    threading.Thread(target=open_browser, daemon=True).start()
    
    # 4. Khởi chạy toàn bộ hệ thống qua Uvicorn
    from backend_api import app
    print("\n[Hệ Thống] Máy chủ đang hoạt động tại: http://127.0.0.1:8000 (Nhấn Ctrl+C để thoát)")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

if __name__ == "__main__":
    main()
