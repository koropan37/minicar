import board
import busio
from digitalio import DigitalInOut, Direction
import adafruit_vl53l4cd
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo
import time

# 1. GPIOの準備 (XSHUTピン)
# 順番: [左外, 左内, 正面, 右内, 右外] と仮定
xshut_pins = [17, 27, 22, 23, 24]
xshuts = []

for pin in xshut_pins:
    gpio = DigitalInOut(getattr(board, f"D{pin}"))
    gpio.direction = Direction.OUTPUT
    gpio.value = False # 一旦すべてOFFにする
    xshuts.append(gpio)

time.sleep(0.1)  # すべてOFFになるのを待つ

# I2Cバスの準備
i2c = board.I2C()
sensors = []

# 2. 1つずつ起こしてアドレスを変更する (アドレス0x30から開始)
base_address = 0x30
for i, xshut in enumerate(xshuts):
    xshut.value = True # センサをON
    time.sleep(0.05)   # 起動を確実に待つ
    
    try:
        # 新しいセンサインスタンスを作成 (最初は必ず0x29にいる)
        sensor = adafruit_vl53l4cd.VL53L4CD(i2c)
        
        # アドレスを変更
        new_address = base_address + i
        sensor.set_address(new_address)
        time.sleep(0.01)
        
        # センサーの設定
        sensor.timing_budget = 50
        sensor.inter_measurement = 60
        
        # 距離測定を開始
        sensor.start_ranging()
        sensors.append(sensor)
        print(f"Sensor {i} initialized at address {hex(new_address)}")
    except Exception as e:
        print(f"Error initializing sensor {i}: {e}")
        # エラーが出たセンサーはスキップ
        continue

if len(sensors) == 0:
    print("エラー: センサーが1つも初期化できませんでした")
    exit(1)

print(f"{len(sensors)}個のセンサーが初期化されました")

# 3. PCA9685とモーター/サーボの設定
pca = PCA9685(i2c)
pca.frequency = 50

# サーボ設定（実測値: 真直ぐ114度, 左92度, 右140度）
steering_servo = servo.Servo(pca.channels[0], min_pulse=500, max_pulse=2500)
SERVO_CENTER = 114  # 真っ直ぐ
SERVO_LEFT = 92     # 左
SERVO_RIGHT = 140   # 右

# ESC設定（実測値: 前進0.23, 後退-0.13）
motor_esc = servo.ContinuousServo(pca.channels[1], min_pulse=1100, max_pulse=2000)
THROTTLE_FORWARD = 0.30   # 前進開始
THROTTLE_BACKWARD = -0.13 # 後退開始
THROTTLE_NEUTRAL = 0.0    # 停止

# 初期位置
steering_servo.angle = SERVO_CENTER
motor_esc.throttle = THROTTLE_NEUTRAL
time.sleep(0.5)

# 4. メインループ
try:
    while True:
        # 全センサのデータを取得
        distances = []
        for idx, sensor in enumerate(sensors):
            try:
                # タイムアウト付きでデータ待ち
                timeout = 0
                while not sensor.data_ready:
                    time.sleep(0.001)
                    timeout += 1
                    if timeout > 100:  # 100ms タイムアウト
                        print(f"Sensor {idx} timeout")
                        distances.append(999)
                        break
                else:
                    sensor.clear_interrupt()
                    dist = sensor.distance
                    # 無効な値は大きな値に置き換え
                    if dist == 0 or dist is None:
                        dist = 999
                    distances.append(dist)
            except Exception as e:
                print(f"Error reading sensor {idx}: {e}")
                distances.append(999)
        
        # センサー数が足りない場合は999で埋める
        while len(distances) < 5:
            distances.append(999)

        # 変数に割り当て (cm単位)
        L2, L1, C, R1, R2 = distances[:5]

        # --- 制御ロジック ---
        
        # ハンドル計算 (右 - 左)
        # 左が狭い → 右へ曲がる（角度を大きく）
        # 右が狭い → 左へ曲がる（角度を小さく）
        left_distance = (L1 + L2) / 2
        right_distance = (R1 + R2) / 2
        
        # ステアリング誤差（正 = 左へ、負 = 右へ）
        steering_error = right_distance - left_distance
        
        # サーボの角度を決定（センターは114度）
        # 係数は感度調整（要実験）
        steering_gain = 0.3  # 調整可能
        servo_angle = SERVO_CENTER + (steering_error * steering_gain)
        
        # 制限 (左92度〜右140度)
        servo_angle = max(SERVO_LEFT, min(SERVO_RIGHT, servo_angle))

        # スピード計算
        # 正面が近いほど遅くする
        if C < 20:  # 20cm以内なら停止・バック
            throttle = THROTTLE_BACKWARD
        elif C < 50:  # 50cm以内なら減速
            # 20cm → 0.0, 50cm → THROTTLE_FORWARD
            throttle = (C - 20) / 30 * THROTTLE_FORWARD
        else:
            throttle = THROTTLE_FORWARD

        print(f"Dist[L2={L2:.0f} L1={L1:.0f} C={C:.0f} R1={R1:.0f} R2={R2:.0f}] | Steer: {servo_angle:.1f}° | Speed: {throttle:.2f}")
        
        # モーター制御
        steering_servo.angle = servo_angle
        motor_esc.throttle = throttle
        
        time.sleep(0.05)  # 20Hzで制御

except KeyboardInterrupt:
    print("\nStop")
finally:
    # 安全停止
    motor_esc.throttle = THROTTLE_NEUTRAL
    steering_servo.angle = SERVO_CENTER
    pca.deinit()
    print("終了しました")