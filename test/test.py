import time
from board import SCL, SDA
import busio
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo

# I2Cバスの作成
i2c = busio.I2C(SCL, SDA)
pca = PCA9685(i2c)
pca.frequency = 50  # ラジコン用は50Hz

# チャンネル0: ハンドル (ステアリングサーボ)
steering = servo.Servo(pca.channels[0])

# チャンネル1: アクセル (ESC)
# ESCもサーボと同じ信号で動きます。「連続回転サーボ」として扱うのが一般的です
throttle = servo.ContinuousServo(pca.channels[1])

print("開始します... (Ctrl+Cで停止)")

try:
    # --- 初期化 ---
    print("ニュートラル (停止)")
    steering.angle = 90       # ハンドル真っ直ぐ
    throttle.throttle = 0.66   # アクセルオフ (0.0が停止)
    time.sleep(2)

    # --- ハンドル操作 ---
    print("右へ！")
    steering.angle = 120      # 角度は現物に合わせて調整してください
    time.sleep(1)

    print("左へ！")
    steering.angle = 60
    time.sleep(1)
    
    print("ハンドル戻す")
    steering.angle = 90
    time.sleep(1)

    # --- アクセル操作 (※タイヤ注意！) ---
    print("ゆっくり前進")
    throttle.throttle = 0.1   # 0.0〜1.0で前進速度
    time.sleep(2)

    print("停止")
    throttle.throttle = 0.0
    time.sleep(1)

    print("ゆっくり後退")
    throttle.throttle = -0.1  # -1.0〜0.0で後退速度
    time.sleep(2)

    print("停止")
    throttle.throttle = 0.0

except KeyboardInterrupt:
    # 終了処理
    throttle.throttle = 0.0
    pca.deinit()
    print("\n安全に終了しました")