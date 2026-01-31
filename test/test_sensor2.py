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
THROTTLE_FORWARD_MAX = 0.33   # 前進最大
THROTTLE_FORWARD_MIN = 0.25   # 前進最小
THROTTLE_BACKWARD = -0.13     # 後退
THROTTLE_NEUTRAL = 0.0        # 停止

# 制御パラメータ
DISTANCE_EMERGENCY = 15    # 15cm以内：緊急停止・バック
DISTANCE_SLOW = 30         # 30cm以内：減速
DISTANCE_NORMAL = 60       # 60cm以内：通常走行
DISTANCE_FAST = 100        # 100cm以上：高速走行

STEERING_GAIN = 0.5        # ステアリング感度（大きいほど敏感）
STEERING_SMOOTH = 0.3      # ステアリングの滑らかさ（0.0-1.0）

# 初期位置
steering_servo.angle = SERVO_CENTER
motor_esc.throttle = THROTTLE_NEUTRAL
time.sleep(0.5)

# 前回のステアリング角度（スムージング用）
prev_servo_angle = SERVO_CENTER

# 4. メインループ
try:
    print("\n自動運転開始")
    print("Ctrl+C で停止")
    
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
                distances.append(999)
        
        # センサー数が足りない場合は999で埋める
        while len(distances) < 5:
            distances.append(999)

        # 変数に割り当て (cm単位)
        L2, L1, C, R1, R2 = distances[:5]

        # --- 制御ロジック（真っ直ぐ走行優先版） ---
        
        # 1. ステアリング計算（基本は真っ直ぐ）
        servo_angle = SERVO_CENTER  # デフォルトは真っ直ぐ
        status = "STRAIGHT"
        
        # 横壁チェック（近すぎる場合のみ回避）
        WALL_TOO_CLOSE = 15  # 15cm以内なら回避
        
        if L2 < WALL_TOO_CLOSE or L1 < WALL_TOO_CLOSE:
            # 左壁が近すぎる → 右に避ける
            servo_angle = SERVO_RIGHT  # 右へ
            status = "AVOID_LEFT"
        elif R2 < WALL_TOO_CLOSE or R1 < WALL_TOO_CLOSE:
            # 右壁が近すぎる → 左に避ける
            servo_angle = SERVO_LEFT  # 左へ
            status = "AVOID_RIGHT"
        
        # 制限 (左92度〜右140度)
        servo_angle = max(SERVO_LEFT, min(SERVO_RIGHT, servo_angle))

        # 2. スピード計算（正面の距離のみで判断）
        if C < DISTANCE_EMERGENCY:
            # 緊急停止・バック
            throttle = THROTTLE_BACKWARD
            status = "BACK"
        elif C < DISTANCE_SLOW:
            # 減速（距離に比例）
            throttle_ratio = (C - DISTANCE_EMERGENCY) / (DISTANCE_SLOW - DISTANCE_EMERGENCY)
            throttle = THROTTLE_FORWARD_MIN * throttle_ratio
            status = "SLOW"
        elif C < DISTANCE_NORMAL:
            # 通常走行
            throttle_ratio = (C - DISTANCE_SLOW) / (DISTANCE_NORMAL - DISTANCE_SLOW)
            throttle = THROTTLE_FORWARD_MIN + (THROTTLE_FORWARD_MAX - THROTTLE_FORWARD_MIN) * throttle_ratio * 0.7
            status = "NORMAL"
        else:
            # 高速走行
            throttle = THROTTLE_FORWARD_MAX
            status = "FAST"

        # デバッグ表示
        print(f"[{status:10s}] Dist[L2={L2:3.0f} L1={L1:3.0f} C={C:3.0f} R1={R1:3.0f} R2={R2:3.0f}] | Steer:{servo_angle:5.1f}° | Speed:{throttle:+.2f}")
        
        # モーター制御
        steering_servo.angle = servo_angle
        motor_esc.throttle = throttle
        
        time.sleep(0.05)  # 20Hz

except KeyboardInterrupt:
    print("\n停止中...")
finally:
    # 安全停止
    motor_esc.throttle = THROTTLE_NEUTRAL
    steering_servo.angle = SERVO_CENTER
    time.sleep(0.2)
    pca.deinit()
    print("終了しました")