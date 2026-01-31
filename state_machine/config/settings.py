"""
状態機械ベース走行の設定ファイル
コース: 約10m×5.5m、中央に島あり、左手法で周回
"""

# ===========================================
# センサー設定 (VL53L4CD)
# ===========================================
# センサー配置: [真左, 斜め左前, 正面, 斜め右前, 真右]
# インデックス:    0       1       2       3        4
XSHUT_PINS = [17, 27, 22, 23, 24]

# センサーI2Cアドレスのベース
SENSOR_BASE_ADDRESS = 0x30

# センサータイミング設定
SENSOR_TIMING_BUDGET = 50
SENSOR_INTER_MEASUREMENT = 60

# センサー無効値 (mm)
SENSOR_INVALID_VALUE = 9999
SENSOR_MAX_RANGE = 1300  # VL53L4CDの最大測定距離 (mm)

# ===========================================
# サーボ設定 (ステアリング)
# ===========================================
SERVO_CHANNEL = 0
SERVO_MIN_PULSE = 500
SERVO_MAX_PULSE = 2500

# ステアリング角度（実測値）
SERVO_CENTER = 114  # 真っ直ぐ
SERVO_LEFT = 92     # 左いっぱい
SERVO_RIGHT = 140   # 右いっぱい

# ステアリング補助値（微調整用）
SERVO_SLIGHT_LEFT = 105   # やや左
SERVO_SLIGHT_RIGHT = 123  # やや右

# ===========================================
# ESC設定 (モーター)
# ===========================================
ESC_CHANNEL = 1
ESC_MIN_PULSE = 1100
ESC_MAX_PULSE = 2000

# スロットル値（実測値: -1.0 ~ 1.0）
THROTTLE_STOP = 0.0
THROTTLE_SLOW = 0.23      # 低速（コーナー、慎重走行）
THROTTLE_NORMAL = 0.30    # 通常
THROTTLE_FAST = 0.38      # 高速（直線）
THROTTLE_REVERSE = -0.15  # 後退

# ===========================================
# PCA9685設定
# ===========================================
PCA9685_FREQUENCY = 50

# ===========================================
# 状態機械パラメータ
# ===========================================

# --- 距離閾値 (mm) ---
# 壁検出
WALL_VERY_CLOSE = 100     # 非常に近い（緊急）
WALL_CLOSE = 200          # 近い
WALL_MEDIUM = 350         # 中距離
WALL_FAR = 500            # 遠い
WALL_NONE = 800           # 壁なし判定

# 左壁沿い走行の目標距離
TARGET_LEFT_DISTANCE = 250  # 左壁との理想距離 (mm)
WALL_FOLLOW_TOLERANCE = 50  # 許容誤差 (mm)

# --- 状態遷移タイマー (秒) ---
TURN_MIN_DURATION = 0.3     # 最小旋回時間
TURN_MAX_DURATION = 2.0     # 最大旋回時間（タイムアウト）
CORNER_EXIT_DELAY = 0.2     # コーナー脱出後の安定待ち

# --- センサーパターン閾値 ---
# コーナー検出用の組み合わせ判定
FRONT_BLOCKED_THRESHOLD = 300       # 正面が塞がれていると判断
LEFT_CORNER_OPEN_THRESHOLD = 600    # 左コーナー検出（左が開けた）
RIGHT_WALL_CLOSE_THRESHOLD = 250    # 右壁が近い

# ===========================================
# 制御周期設定
# ===========================================
CONTROL_INTERVAL = 0.04  # 40ms (25Hz) - 少し高速化

# ===========================================
# デバッグ設定
# ===========================================
DEBUG_PRINT_INTERVAL = 5  # N回に1回デバッグ表示
ENABLE_DEBUG_LOG = True
LOG_STATE_CHANGES = True  # 状態遷移をログ出力
