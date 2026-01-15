import time
import board
from adafruit_vl53l4cd import VL53L4CD
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo

# --- 設定 ---
MIN_DIST = 5.0   # これより近いと0度 (cm)
MAX_DIST = 30.0  # これより遠いと180度 (cm)

# 1. I2Cの準備
i2c = board.I2C()

# 2. 距離センサーの準備
vl53 = VL53L4CD(i2c)
vl53.start_ranging()

# 3. サーボドライバ(PCA9685)の準備
pca = PCA9685(i2c)
pca.frequency = 50 # サーボは通常50Hz

# 4. サーボモーターの準備
# 写真では一番左端(チャンネル0)に繋がっていると想定しています
servo_motor = servo.Servo(pca.channels[0])

print("システム開始: センサーに手を近づけたり遠ざけたりしてください")

try:
    while True:
        # センサーのデータ待ち
        while not vl53.data_ready:
            pass
        vl53.clear_interrupt()
        
        current_dist = vl53.distance
        
        # --- 距離を角度に変換する計算 ---
        if current_dist < MIN_DIST:
            angle = 0
        elif current_dist > MAX_DIST:
            angle = 180
        else:
            # 5cm〜30cmの間を 0〜180度に割り当てる計算
            # (今の距離 - 最小距離) ÷ (範囲) × 180度
            angle = (current_dist - MIN_DIST) / (MAX_DIST - MIN_DIST) * 180

        # サーボを動かす
        servo_motor.angle = angle
        
        print(f"距離: {current_dist:.1f} cm -> 角度: {int(angle)} 度")
        
        time.sleep(0.05)

except KeyboardInterrupt:
    # 終了時にモーターの力を抜く
    pca.deinit()
    print("\n終了します")