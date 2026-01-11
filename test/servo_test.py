import time
from board import SCL, SDA
import busio
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo

# I2Cバスの作成
i2c = busio.I2C(SCL, SDA)

# PCA9685クラスのインスタンス作成
pca = PCA9685(i2c)
pca.frequency = 50  # サーボ用は通常50Hz

# チャンネル0にサーボが繋がっているとする
servo0 = servo.Servo(pca.channels[0])

print("サーボを動かします...")

try:
    while True:
        # 0度へ
        print("0度")
        servo0.angle = 0
        time.sleep(1)

        # 90度へ
        print("90度")
        servo0.angle = 90
        time.sleep(1)

        # 180度へ
        print("180度")
        servo0.angle = 180
        time.sleep(1)

except KeyboardInterrupt:
    # Ctrl+Cで終了時にモータの力を抜く
    pca.deinit()
    print("\n終了しました")