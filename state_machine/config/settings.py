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
THROTTLE_SLOW = 0.26      # 低速旋回用
THROTTLE_NORMAL = 0.35    
THROTTLE_FAST = 0.40      
THROTTLE_REVERSE = -0.12  

# ===========================================
# PCA9685設定
# ===========================================
PCA9685_FREQUENCY = 50

# ===========================================
# 状態機械パラメータ
# ===========================================

# --- 距離閾値 (mm) ---
# 壁検出
WALL_VERY_CLOSE = 150     # 非常に近い（緊急）
WALL_CLOSE = 250          # 近い
WALL_MEDIUM = 400         # 中距離
WALL_FAR = 700            # 遠い
WALL_NONE = 1000          # 壁なし判定

# 左壁沿い走行の目標距離
TARGET_LEFT_DISTANCE = 400  
WALL_FOLLOW_TOLERANCE = 150 

# --- 状態遷移タイマー (秒) ---
TURN_MIN_DURATION = 1.0     # 最小旋回時間 (しっかり曲がるために長めに設定)
TURN_MAX_DURATION = 3.0     
CORNER_EXIT_DELAY = 0.3     

# --- センサーパターン閾値 ---
# コーナー検出用の組み合わせ判定
FRONT_BLOCKED_THRESHOLD = 800       # 正面が塞がれている (80cm手前から右折開始)
LEFT_CORNER_OPEN_THRESHOLD = 1000   
RIGHT_WALL_CLOSE_THRESHOLD = 300    

# S字区間検出
S_CURVE_DETECTION_THRESHOLD = 700   

# ===========================================
# 制御周期設定
# ===========================================
CONTROL_INTERVAL = 0.04  # 40ms (25Hz)

# ===========================================
# デバッグ設定
# ===========================================
DEBUG_PRINT_INTERVAL = 1  
ENABLE_DEBUG_LOG = True
LOG_STATE_CHANGES = True