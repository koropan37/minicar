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
esc = servo.ContinuousServo(pca.channels[1], min_pulse=1000, max_pulse=2000)

def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

print("【ニュートラル位置探し】")
print("u: 数値を上げる (+0.01)")
print("d: 数値を下げる (-0.01)")
print("q: 終了")

current_val = 0.66 # まず0.0からスタート
esc.throttle = current_val

try:
    while True:
        print(f"\r現在のthrottle値: {current_val:.2f}  <-- これで止まったらメモ！", end="")
        key = getch()
        
        if key == 'u':
            current_val += 0.01
        elif key == 'd':
            current_val -= 0.01
        elif key == 'q':
            break
            
        # 安全のため範囲制限
        if current_val > 1.0: current_val = 1.0
        if current_val < -1.0: current_val = -1.0
        
        esc.throttle = current_val
        time.sleep(0.05)

except KeyboardInterrupt:
    pass

esc.throttle = 0.0 # 終了時はとりあえず0に戻す
pca.deinit()
print("\n終了")