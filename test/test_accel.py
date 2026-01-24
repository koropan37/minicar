import time, busio
from board import SCL, SDA
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo

i2c = busio.I2C(SCL, SDA)
pca = PCA9685(i2c); pca.frequency = 50
esc = servo.ContinuousServo(pca.channels[1], min_pulse=1000, max_pulse=2000)

try:
    for v in [1.0, 0.9, 0.8, 0.7, 0.66, 0.65, 0.64, 0.63, 0.6, 0.5, 0.0, -0.5, -1.0]:
        print(f"set throttle = {v}")
        esc.throttle = v
        time.sleep(2)  # 観察用に十分な時間
finally:
    esc.throttle = 0.0
    pca.deinit()
    print("終了")