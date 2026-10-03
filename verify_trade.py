"""
Công cụ kiểm chứng độc lập (Independent Trade Verifier)
Giúp người dùng kiểm tra chi tiết từng bước di chuyển nến của bất kỳ lệnh nào trong Backtest
để xác thực không có hiện tượng gian lận tương lai (No Lookahead Bias) và khớp giá chuẩn xác.
"""
import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd

def verify_trade(ticket_number: int = None, csv_path: str = "backtest_trades_v2.csv"):
    df_trades = pd.read_csv(csv_path)
    if df_trades.empty:
        print("[Lỗi] File nhật ký lệnh trống!")
        return
        
    if ticket_number is None:
        # Chọn ngẫu nhiên 1 lệnh thắng và 1 lệnh thua để đối chiếu
        win_sample = df_trades[df_trades['Profit_USD'] > 0].iloc[0]
        loss_sample = df_trades[df_trades['Profit_USD'] < 0].iloc[0] if len(df_trades[df_trades['Profit_USD'] < 0]) > 0 else None
        samples = [win_sample]
        if loss_sample is not None:
            samples.append(loss_sample)
    else:
        matched = df_trades[df_trades['Ticket'] == ticket_number]
        if matched.empty:
            print(f"[Lỗi] Không tìm thấy vé #{ticket_number}")
            return
        samples = [matched.iloc[0]]
        
    df_candles = pd.read_csv("xauusd_m5.csv")
    df_candles['time'] = pd.to_datetime(df_candles['time'])
    
    for s in samples:
        print("\n" + "=" * 70)
        print(f"       KIỂM CHỨNG LỆNH #{s['Ticket']} ({s['Stage']})")
        print("=" * 70)
        print(f"  Loại lệnh         : {s['Type']}")
        print(f"  Thời gian vào     : {s['Entry_Time']}")
        print(f"  Giá vào (Entry)   : {s['Entry_Price']:.2f}")
        print(f"  Khối lượng        : {s['Lot']} lot")
        print(f"  Thời gian đóng    : {s['Exit_Time']}")
        print(f"  Giá đóng (Exit)   : {s['Exit_Price']:.2f}")
        print(f"  Lợi nhuận         : ${s['Profit_USD']:+,.2f} USD")
        print(f"  Lý do thoát lệnh  : {s['Exit_Reason']}")
        print("-" * 70)
        print("  ĐỐI CHIẾU DỮ LIỆU NẾN THỰC TẾ TRÊN MT5:")
        
        entry_t = pd.to_datetime(s['Entry_Time'])
        exit_t = pd.to_datetime(s['Exit_Time'])
        
        subset = df_candles[(df_candles['time'] >= entry_t) & (df_candles['time'] <= exit_t)]
        print(f"  Tổng số nến giữ lệnh: {len(subset)} nến M5")
        if not subset.empty:
            print(f"  - Nến vào lệnh : Open={subset.iloc[0]['open']}, High={subset.iloc[0]['high']}, Low={subset.iloc[0]['low']}, Close={subset.iloc[0]['close']}")
            print(f"  - Nến đóng lệnh: Open={subset.iloc[-1]['open']}, High={subset.iloc[-1]['high']}, Low={subset.iloc[-1]['low']}, Close={subset.iloc[-1]['close']}")
            if s['Type'] == 'BUY':
                print(f"  - Đỉnh cao nhất đạt được trong lúc giữ: {subset['high'].max():.2f}")
                print(f"  - Đáy thấp nhất chịu đựng trong lúc giữ : {subset['low'].min():.2f}")
            else:
                print(f"  - Đáy sâu nhất đạt được trong lúc giữ : {subset['low'].min():.2f}")
                print(f"  - Đỉnh cao nhất chịu đựng trong lúc giữ : {subset['high'].max():.2f}")
        print("=" * 70)

if __name__ == "__main__":
    verify_trade()
