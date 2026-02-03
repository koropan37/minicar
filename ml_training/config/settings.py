"""
機械学習の設定ファイル

【モデルタイプ一覧】
┌─────────────────┬────────────────────────────────────────────────────────┐
│ モデルタイプ     │ 説明                                                    │
├─────────────────┼────────────────────────────────────────────────────────┤
│ mlp_regressor   │ 多層パーセプトロン（回帰）                               │
│                 │ - 連続値（-1.0〜1.0）を予測                              │
│                 │ - 滑らかなステアリング制御が可能                          │
│                 │ - データ量: 1000件以上推奨                               │
├─────────────────┼────────────────────────────────────────────────────────┤
│ mlp_classifier  │ 多層パーセプトロン（分類）                               │
│                 │ - クラス（左/直進/右など）を予測                          │
│                 │ - シンプルで少ないデータでも動作                          │
│                 │ - データ量: 300件以上推奨                                │
├─────────────────┼────────────────────────────────────────────────────────┤
│ random_forest   │ ランダムフォレスト                                       │
│                 │ - 決定木のアンサンブル学習                               │
│                 │ - 過学習しにくく安定                                     │
│                 │ - ハイパーパラメータ調整が少なくて済む                    │
└─────────────────┴────────────────────────────────────────────────────────┘
"""

# ===========================================
# プリセット選択（"small", "medium", "large", "custom"）
# ===========================================
PRESET = "small"

# プリセット定義
_PRESETS = {
    "small": {
        "model_type": "mlp_classifier",
        "hidden_layers": (32, 32),
        "target_columns": ["steering"],
    },
    "medium": {
        "model_type": "mlp_regressor",
        "hidden_layers": (64, 64),
        "target_columns": ["steering", "throttle"],
    },
    "large": {
        "model_type": "mlp_regressor",
        "hidden_layers": (128, 128, 64),
        "target_columns": ["steering", "throttle"],
    },
}

# ===========================================
# データ設定
# ===========================================
RAW_DATA_PATH = "data/raw"
PROCESSED_DATA_PATH = "data/processed"
MODEL_SAVE_PATH = "models"

# CSVカラム
CSV_COLUMNS = ["timestamp", "steering", "throttle", "L2", "L1", "C", "R1", "R2"]
SENSOR_COLUMNS = ["L2", "L1", "C", "R1", "R2"]

# 予測対象カラム
TARGET_COLUMNS = ["steering", "throttle"]

# ===========================================
# 前処理設定
# ===========================================
SENSOR_MIN = 0
SENSOR_MAX = 1000
SENSOR_INVALID = 999
NORMALIZATION = "standard"

# ===========================================
# モデル設定（PRESET="custom"の場合に使用）
# ===========================================
MODEL_TYPE = "mlp_regressor"
HIDDEN_LAYERS = (64, 64, 32)
MAX_ITER = 2000
RANDOM_STATE = 42
TEST_SIZE = 0.2

# ===========================================
# 分類モデル用設定（mlp_classifierの場合）
# ===========================================
STEER_THRESHOLDS = {
    "hard_left": -0.6,
    "left": -0.2,
    "straight": 0.2,
    "right": 0.6,
}

CLASS_NAMES = ["hard_left", "left", "straight", "right", "hard_right"]

# ===========================================
# 実車走行用設定（run_ml.py用）
# ===========================================

# --- センサー設定 (VL53L4CD) ---
XSHUT_PINS = [17, 27, 22, 23, 24]  # [真左, 斜め左前, 正面, 斜め右前, 真右]
SENSOR_BASE_ADDRESS = 0x30
SENSOR_TIMING_BUDGET = 20  # 高速化のため20ms
SENSOR_INTER_MEASUREMENT = 0
SENSOR_INVALID_VALUE = 9999
SENSOR_MAX_RANGE = 1300  # mm

# --- サーボ設定 (ステアリング) ---
SERVO_CHANNEL = 0
SERVO_MIN_PULSE = 500
SERVO_MAX_PULSE = 2500

# ステアリング角度
SERVO_CENTER = 114
SERVO_LEFT = 92
SERVO_RIGHT = 140

# --- ESC設定 (モーター) ---
ESC_CHANNEL = 1
ESC_MIN_PULSE = 1100
ESC_MAX_PULSE = 2000

# スロットル値
THROTTLE_STOP = 0.0
THROTTLE_SLOW = 0.28
THROTTLE_NORMAL = 0.35
THROTTLE_FAST = 0.40

# --- PCA9685設定 ---
PCA9685_ADDRESS = 0x40
PCA9685_FREQUENCY = 50

# --- 走行制御パラメータ ---
EMERGENCY_STOP_DISTANCE = 0    # 100 → 0（無効化）
SLOW_DOWN_DISTANCE = 150       # 300 → 150
CONTROL_INTERVAL = 0.04        # 制御周期 (25Hz)
DEBUG_PRINT_INTERVAL = 5       # デバッグ表示間隔

# ===========================================
# プリセット適用
# ===========================================
if PRESET in _PRESETS:
    _preset = _PRESETS[PRESET]
    MODEL_TYPE = _preset["model_type"]
    HIDDEN_LAYERS = _preset["hidden_layers"]
    TARGET_COLUMNS = _preset["target_columns"]
