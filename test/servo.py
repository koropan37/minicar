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

# 広い範囲を指定
servo0 = servo.Servo(pca.channels[0], min_pulse=500, max_pulse=2500)

print("サーボの中心位置を探します")
print("90度で試して、真っ直ぐでなければ角度を微調整してください")

try:
    # 80度～100度の範囲で試す
    for angle in range(80, 160, 2):
        print(f"{angle}度 (パルス幅: {servo0._pwm_out.duty_cycle})")
        servo0.angle = angle
        time.sleep(1)
    
    # 真っ直ぐになる角度を見つけたら、その値を使う

except KeyboardInterrupt:
    pca.deinit()
    print("\n終了しました")

    #真直 114 左 92 右 140