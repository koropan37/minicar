"""
仮想ポテンシャル法走行の設定ファイル
障害物を反発力として計算し走行する
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

# ===========================================
# ESC設定 (モーター)
# ===========================================
ESC_CHANNEL = 1
ESC_MIN_PULSE = 1100
ESC_MAX_PULSE = 2000

# スロットル値（実測値: -1.0 ~ 1.0）
THROTTLE_STOP = 0.0
THROTTLE_SLOW = 0.26      
THROTTLE_NORMAL = 0.35    
THROTTLE_REVERSE = -0.16  

# ===========================================
# PCA9685設定
# ===========================================
PCA9685_FREQUENCY = 50

# ===========================================
# ポテンシャル法パラメータ
# ===========================================

# センサー毎の重み (反発力の強さ)
# 距離が近いほど力は強くなる: F = Weight / (Distance^2)
WEIGHT_LEFT = 2.0        # 右へ押す力
WEIGHT_FRONT_LEFT = 6.0  # 右へ押す力（強め）
WEIGHT_FRONT = 10.0      # 減速＆旋回用（直接ステアリングへの寄与は左右差による）
WEIGHT_FRONT_RIGHT = 6.0 # 左へ押す力（強め）
WEIGHT_RIGHT = 2.0       # 左へ押す力

# ステアリング計算用
POTENTIAL_STEER_GAIN = 4000.0  # 反発力の合力を角度変化量に変換するゲイン

# スロットル計算用
POTENTIAL_THROTTLE_BASE = THROTTLE_NORMAL
POTENTIAL_THROTTLE_MIN = THROTTLE_SLOW
BRAKE_WEIGHT_FRONT = 15.0     # 正面の障害物による減速効果
BRAKE_WEIGHT_SIDE_FRONT = 5.0 # 斜め前の障害物による減速効果

# 緊急回避
EMERGENCY_DIST = 150     # これより近づいたらバック

# ===========================================
# 制御周期設定
# ===========================================
CONTROL_INTERVAL = 0.04  # 40ms (25Hz)

# ===========================================
# デバッグ設定
# ===========================================
DEBUG_PRINT_INTERVAL = 1  
ENABLE_DEBUG_LOG = True
