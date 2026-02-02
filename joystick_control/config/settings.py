"""
ミニカー制御の設定ファイル
test_sensor.py の設定を参考に作成
"""

# ===========================================
# センサー設定 (VL53L4CD)
# ===========================================
# XSHUTピン番号 [左外, 左内, 正面, 右内, 右外]
XSHUT_PINS = [17, 27, 22, 23, 24]

# センサーI2Cアドレスのベース
SENSOR_BASE_ADDRESS = 0x30

# センサータイミング設定
SENSOR_TIMING_BUDGET = 50
SENSOR_INTER_MEASUREMENT = 60

# センサー無効値
SENSOR_INVALID_VALUE = 999

# ===========================================
# サーボ設定 (ステアリング)
# ===========================================
SERVO_CHANNEL = 0
SERVO_MIN_PULSE = 500
SERVO_MAX_PULSE = 2500

# ステアリング角度（実測値）
SERVO_CENTER = 114  # 真っ直ぐ
SERVO_LEFT = 92     # 左
SERVO_RIGHT = 140   # 右

# ===========================================
# ESC設定 (モーター)
# ===========================================
ESC_CHANNEL = 1
ESC_MIN_PULSE = 1100
ESC_MAX_PULSE = 2000

# スロットル値（実測値）
THROTTLE_FORWARD_MIN = 0.25  # 前進最小（トリガー軽く押し）
THROTTLE_FORWARD_MAX = 0.45  # 前進最大（トリガー全押し）
THROTTLE_BACKWARD_MIN = -0.13  # 後退最小（トリガー軽く押し）
THROTTLE_BACKWARD_MAX = -0.16  # 後退最大（トリガー全押し）
THROTTLE_NEUTRAL = 0.0         # 停止

# ===========================================
# PCA9685設定
# ===========================================
PCA9685_FREQUENCY = 50

# ===========================================
# ジョイスティック設定
# ===========================================
JOYSTICK_DEADZONE = 0.1  # デッドゾーン

# 軸マッピング
AXIS_STEERING = 0  # 左スティック X軸（ステアリング）
AXIS_THROTTLE = 1  # 左スティック Y軸（スロットル）※未使用に変更
AXIS_TRIGGER_LEFT = 2   # 左トリガー（LT）: 後退アクセル
AXIS_TRIGGER_RIGHT = 5  # 右トリガー（RT）: 前進アクセル

# ボタンマッピング
BUTTON_RECORD_START = 0  # Aボタン: 録画開始
BUTTON_RECORD_STOP = 1   # Bボタン: 録画停止
BUTTON_EMERGENCY_STOP = 2  # Xボタン: 緊急停止

# ===========================================
# 録画設定
# ===========================================
RECORD_INTERVAL = 0.05  # 50ms（20Hz）
DATA_SAVE_PATH = "data/record_data.csv"

# CSVヘッダー
CSV_HEADER = ["timestamp", "steering", "throttle", "L2", "L1", "C", "R1", "R2"]
