"""
Launcher khởi động toàn bộ hệ thống Forward Test Real-Time:
- Backend FastAPI + WebSocket MT5 Bridge
- Giao diện Frontend TypeScript Dashboard (Tự động mở trình duyệt tại http://127.0.0.1:8000)
"""
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import os
import time
import webbrowser
import subprocess
import uvicorn

def main():
    print("=" * 70)
    print("    KHỞI ĐỘNG HỆ THỐNG FORWARD TESTING REAL-TIME (MT5 + TS DASHBOARD)")
    print("=" * 70)
    print("  * Backend API: FastAPI + Uvicorn + WebSocket Bridge")
    print("  * Frontend TS: React TypeScript Glassmorphism Dashboard")
    print("  * Địa chỉ Web: http://127.0.0.1:8000")
    print("=" * 70)
    
    # Kiểm tra dist build của frontend
    dist_index = os.path.join(os.path.dirname(__file__), "dashboard", "dist", "index.html")
    if not os.path.exists(dist_index):
        print("[Build] Đang build giao diện TypeScript...")
        subprocess.run(["npm", "--prefix", "dashboard", "run", "build"], shell=True)

    # Mở trình duyệt sau 1.5 giây
    def open_browser():
        time.sleep(1.5)
        print("\n[Trình Duyệt] Đang mở Dashboard tại http://127.0.0.1:8000 ...")
        webbrowser.open("http://127.0.0.1:8000")
        
    import threading
    threading.Thread(target=open_browser, daemon=True).start()

    # Chạy Uvicorn server
    from backend_api import app
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

if __name__ == "__main__":
    main()
