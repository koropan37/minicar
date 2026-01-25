import sys
import tty
import termios
import time
from board import SCL, SDA
import busio
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo

# I2CとPCA9685の設定
i2c = busio.I2C(SCL, SDA)
pca = PCA9685(i2c)
pca.frequency = 50

# ここでmin_pulse, max_pulseを指定
# QUICRUN 1060などの一般的なESC向け設定
# ESCの実動作範囲を完全にカバー
esc = servo.ContinuousServo(pca.channels[1], min_pulse=1100, max_pulse=2000)


THROTTLE_SCALE = 1.0  

def set_throttle(value):
    """throttle値をスケーリングして設定"""
    esc.throttle = value * THROTTLE_SCALE

def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        # Ctrl+C を検出して KeyboardInterrupt を発生させる
        if ch == '\x03':
            raise KeyboardInterrupt
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def auto_find_neutral(start=0.8, end=0.4, step=-0.005, delay=0.5):
    """
    start から end まで step ずつ変更して出力する。
    目視でモーターが止まったと思ったら 's' を押して保存。
    """
    val = start
    print("\n自動スキャン開始: 車輪を外す/固定してから実行")
    print("停止を確認したら 's' を押してその値を保存、'q' で中止")
    try:
        while (step < 0 and val >= end) or (step > 0 and val <= end):
            esc.throttle = val
            print(f"\r試験値: {val:.3f}    ", end="", flush=True)
            # ノンブロッキングでキー読み取り（簡易）
            time.sleep(delay)
            # キーが押されていれば処理（標準入力ブロッキング回避の簡易化）
            import select, sys
            if select.select([sys.stdin], [], [], 0)[0]:
                ch = sys.stdin.read(1)
                if ch == 's':
                    print(f"\n保存: {val:.3f}")
                    return val
                if ch == 'q':
                    print("\n中止")
                    return None
            val += step
    except KeyboardInterrupt:
        print("\nキャンセルされました")
        return None
    return None

print("【ニュートラル位置探し】")
print("u: 数値を上げる (+0.01)")
print("d: 数値を下げる (-0.01)")
print("a: 自動スキャン開始")
print("s: 現在値をニュートラルとして保存して終了")
print("q: 終了（保存なし）")

current_val = 0.0
set_throttle(current_val)
neutral_value = None

try:
    while True:
        print(f"\r現在のthrottle値: {current_val:.2f}  <-- これで止まったら's'を押して保存", end="", flush=True)
        key = getch()
        
        if key == 'u':
            current_val += 0.01
        elif key == 'd':
            current_val -= 0.01
        elif key == 'a':
            # 自動スキャン呼び出し（戻り値を保存候補にする）
            found = auto_find_neutral(start=0.8, end=0.4, step=-0.005, delay=0.6)
            if found is not None:
                neutral_value = found
                print(f"自動検出でニュートラル値を保存: {neutral_value:.3f}")
                break
        elif key == 's':
            neutral_value = current_val
            print(f"\nニュートラル値を保存しました: {neutral_value:.2f}")
            break
        elif key == 'q':
            print("\n終了（保存なし）")
            break
            
        # 範囲制限
        if current_val > 1.0: current_val = 1.0
        if current_val < -1.0: current_val = -1.0
        
        set_throttle(current_val)
        time.sleep(0.05)

except KeyboardInterrupt:
    print("\nKeyboardInterrupt/ctrl+C を検出しました。終了します。")

finally:
    # 終了時に保存値があればそれをニュートラルとして設定、なければ0.0
    try:
        if neutral_value is not None:
            esc.throttle = neutral_value
            print(f"終了: ニュートラル値 {neutral_value:.2f} を設定しました")
        else:
            esc.throttle = 0.0
            print("終了: throttle を 0.0 に戻しました")
    except Exception:
        pass
    pca.deinit()
    print("終了完了")

    #前進 = 0.23 後退 = -0.13