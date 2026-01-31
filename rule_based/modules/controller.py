"""
走行制御モジュール
左壁沿いルールベース走行のロジックを実装

センサー配置:
    [0] 真左      - 左壁との距離（壁沿い走行のメイン）
    [1] 斜め左前  - 左前方の障害物・左コーナー検出
    [2] 正面      - 前方障害物・右コーナー検出
    [3] 斜め右前  - 右前方の障害物検出
    [4] 真右      - 右壁との距離
"""

from enum import Enum
from config.settings import (
    SERVO_CENTER, SERVO_LEFT, SERVO_RIGHT,
    TARGET_WALL_DISTANCE, KP, KD, KI,
    EMERGENCY_FRONT_DISTANCE, EMERGENCY_SIDE_DISTANCE,
    CORNER_FRONT_DISTANCE, CORNER_NO_WALL_DISTANCE, CORNER_WALL_EXIST_DISTANCE,
    STRAIGHT_ERROR_THRESHOLD,
    SPEED_SLOW, SPEED_MEDIUM, SPEED_FAST,
    THROTTLE_NEUTRAL,
    SENSOR_INVALID_VALUE,
    ENABLE_DEBUG_LOG
)


class DrivingState(Enum):
    """走行状態を表す列挙型"""
    EMERGENCY_STOP = 0      # 緊急停止
    EMERGENCY_AVOID = 1     # 緊急回避
    RIGHT_TURN = 2          # 右コーナー（前に壁）
    LEFT_TURN = 3           # 左コーナー（左壁なし）
    WALL_FOLLOW = 4         # 壁沿い走行
    STRAIGHT = 5            # 直進


class DrivingController:
    """
    走行制御クラス
    センサー値から適切なステアリングとスロットルを決定
    """
    
    def __init__(self):
        """コントローラーの初期化"""
        # PID制御用の状態変数
        self.prev_error = 0.0
        self.integral_error = 0.0
        
        # 現在の走行状態
        self.current_state = DrivingState.WALL_FOLLOW
        
        # デバッグ用
        self.loop_count = 0
    
    def compute_control(self, distances):
        """
        センサー距離から制御値を計算
        
        Args:
            distances: [真左, 斜め左前, 正面, 斜め右前, 真右] (mm)
        
        Returns:
            tuple: (steering_angle, throttle_value, state)
        """
        # センサー値を展開（実際の配置に合わせた名前）
        Left, FrontLeft, Center, FrontRight, Right = distances
        
        # 無効値を大きな値に置換（壁なしとして扱う）
        Left = Left if Left < SENSOR_INVALID_VALUE else 2000
        FrontLeft = FrontLeft if FrontLeft < SENSOR_INVALID_VALUE else 2000
        Center = Center if Center < SENSOR_INVALID_VALUE else 2000
        FrontRight = FrontRight if FrontRight < SENSOR_INVALID_VALUE else 2000
        Right = Right if Right < SENSOR_INVALID_VALUE else 2000
        
        # デフォルト値
        steering = SERVO_CENTER
        throttle = SPEED_SLOW
        state = DrivingState.WALL_FOLLOW
        
        # ==========================================
        # 状態判定（優先度順）
        # ==========================================
        
        # 【1. 緊急停止】正面が非常に近い
        if Center < EMERGENCY_FRONT_DISTANCE:
            state = DrivingState.EMERGENCY_STOP
            steering = SERVO_CENTER
            throttle = THROTTLE_NEUTRAL
            self._reset_pid()
        
        # 【2. 緊急回避】斜め前方が非常に近い
        elif FrontLeft < EMERGENCY_SIDE_DISTANCE or FrontRight < EMERGENCY_SIDE_DISTANCE:
            state = DrivingState.EMERGENCY_AVOID
            if FrontLeft < FrontRight:
                # 左前が近い → 右へ避ける
                steering = SERVO_RIGHT
            else:
                # 右前が近い → 左へ避ける
                steering = SERVO_LEFT
            throttle = SPEED_SLOW
            self._reset_pid()
        
        # 【3. 右コーナー】正面または斜め右前に壁がある
        elif Center < CORNER_FRONT_DISTANCE or FrontRight < CORNER_FRONT_DISTANCE * 0.8:
            state = DrivingState.RIGHT_TURN
            steering = SERVO_RIGHT
            throttle = SPEED_SLOW
            self._reset_pid()
        
        # 【4. 左コーナー】左壁がなくなった（斜め左前で早期検出）
        # 斜め左前が遠い AND 真左も遠い → 左コーナー
        elif FrontLeft > CORNER_NO_WALL_DISTANCE and Left > CORNER_WALL_EXIST_DISTANCE:
            state = DrivingState.LEFT_TURN
            steering = SERVO_LEFT
            throttle = SPEED_SLOW
            self._reset_pid()
        
        # 【5. 壁沿い走行】PD制御
        else:
            # 真左のセンサーで壁との距離を維持
            # 斜め左前も参考にして、壁に近づきすぎを早期検出
            wall_distance = Left
            
            # 斜め左前が近い場合は、壁に寄りすぎている可能性
            if FrontLeft < Left * 0.8 and FrontLeft < TARGET_WALL_DISTANCE:
                # 斜め左前の値を重視（壁に向かっている）
                wall_distance = FrontLeft * 0.9
            
            # PD制御の計算
            steering, error = self._compute_pid(wall_distance)
            
            # 誤差が小さく、前方が開けていれば直進モードで速度アップ
            if abs(error) < STRAIGHT_ERROR_THRESHOLD and Center > CORNER_FRONT_DISTANCE * 1.5:
                state = DrivingState.STRAIGHT
                throttle = SPEED_FAST
            else:
                state = DrivingState.WALL_FOLLOW
                throttle = SPEED_MEDIUM
        
        self.current_state = state
        return steering, throttle, state
    
    def _compute_pid(self, wall_distance):
        """
        PD制御によるステアリング計算
        
        Args:
            wall_distance: 左壁との距離 (mm)
        
        Returns:
            tuple: (steering_angle, error)
        """
        # 誤差計算（目標より近い=正, 遠い=負）
        error = TARGET_WALL_DISTANCE - wall_distance
        
        # 微分項（誤差の変化率）
        derivative = error - self.prev_error
        
        # 積分項（通常は使用しない）
        self.integral_error += error
        # 積分項の飽和防止
        self.integral_error = max(-1000, min(1000, self.integral_error))
        
        # PID出力
        correction = (KP * error) + (KD * derivative) + (KI * self.integral_error)
        
        # ステアリング角度に変換
        # 壁に近い(error正) → 右へ行きたい → 角度を大きくする
        # 壁が遠い(error負) → 左へ行きたい → 角度を小さくする
        steering = SERVO_CENTER + correction
        
        # 範囲制限
        steering = max(SERVO_LEFT, min(SERVO_RIGHT, steering))
        
        # 状態を保存
        self.prev_error = error
        
        return steering, error
    
    def _reset_pid(self):
        """PID制御の状態をリセット"""
        self.prev_error = 0.0
        self.integral_error = 0.0
    
    def get_state_name(self):
        """現在の走行状態を文字列で取得"""
        state_names = {
            DrivingState.EMERGENCY_STOP: "緊急停止",
            DrivingState.EMERGENCY_AVOID: "緊急回避",
            DrivingState.RIGHT_TURN: "右コーナー",
            DrivingState.LEFT_TURN: "左コーナー",
            DrivingState.WALL_FOLLOW: "壁沿い",
            DrivingState.STRAIGHT: "直進",
        }
        return state_names.get(self.current_state, "不明")
    
    def format_debug_info(self, distances, steering, throttle):
        """デバッグ情報を整形"""
        Left, FrontLeft, Center, FrontRight, Right = distances
        return (
            f"[{self.get_state_name():6}] "
            f"L:{Left:4.0f} FL:{FrontLeft:4.0f} C:{Center:4.0f} FR:{FrontRight:4.0f} R:{Right:4.0f} | "
            f"Steer:{steering:5.1f} Thr:{throttle:.2f}"
        )
