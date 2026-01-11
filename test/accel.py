import time
from board import SCL, SDA
import busio
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo

i2c = busio.I2C(SCL, SDA)
pca = PCA9685(i2c)
pca.frequency = 50

# ESCの設定（パルス幅の微調整）
# 一般的なラジコン用ESCのパルス幅は min=1000, max=2000 くらいです
esc = servo.ContinuousServo(pca.channels[1], min_pulse=1000, max_pulse=2000)

print("調整モード開始")
print("今の値でタイヤが止まれば、それが『真のニュートラル』です")

try:
    # パターンA：完全に0.0
    print("【0.0】を送ります...")
    esc.throttle = 0.0
    time.sleep(3)

    # パターンB：少しプラス（0.05）
    print("【0.05】を送ります...")
    esc.throttle = 0.05
    time.sleep(3)

    # パターンC：少しマイナス（-0.05）
    print("【-0.05】を送ります...")
    esc.throttle = -0.05
    time.sleep(3)

    # 最後に停止を試みる
    esc.throttle = 0.0

except KeyboardInterrupt:
    esc.throttle = 0.0
    pca.deinit()