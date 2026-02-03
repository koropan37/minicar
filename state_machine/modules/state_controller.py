"""
状態機械ベースの走行制御モジュール
左手法（左壁沿い）で周回

状態遷移図:
    ┌─────────────────────────────────────────────────┐
    │                                                 │
    v                                                 │
  [INIT] ──> [WALL_FOLLOW] ──┬──> [LEFT_TURN] ───────┤
                │            │                        │
                │            └──> [RIGHT_TURN] ──────┤
                │                                     │
                └──> [EMERGENCY] ──> [RECOVER] ──────┘
"""

import time
from enum import Enum, auto

from config.settings import (
    SERVO_CENTER, SERVO_LEFT, SERVO_RIGHT,
    SERVO_SLIGHT_LEFT, SERVO_SLIGHT_RIGHT,
    THROTTLE_STOP, THROTTLE_SLOW, THROTTLE_NORMAL, THROTTLE_FAST, THROTTLE_REVERSE,
    WALL_VERY_CLOSE, WALL_CLOSE, WALL_MEDIUM, WALL_FAR, WALL_NONE,
    TARGET_LEFT_DISTANCE, WALL_FOLLOW_TOLERANCE,
    TURN_MIN_DURATION, TURN_MAX_DURATION, CORNER_EXIT_DELAY,
    FRONT_BLOCKED_THRESHOLD, LEFT_CORNER_OPEN_THRESHOLD, RIGHT_WALL_CLOSE_THRESHOLD,
    SENSOR_INVALID_VALUE,
    LOG_STATE_CHANGES,
    S_CURVE_DETECTION_THRESHOLD
)


class State(Enum):
    """走行状態"""
    INIT = auto()           # 初期化
    WALL_FOLLOW = auto()    # 左壁沿い走行
    LEFT_TURN = auto()      # 左コーナー（左壁が開けた）
    RIGHT_TURN = auto()     # 右コーナー（前方に壁）
    EMERGENCY = auto()      # 緊急回避
    RECOVER = auto()        # リカバリー（後退など）
    STOPPED = auto()        # 停止


class StateController:
    """
    状態機械ベースの走行制御
    
    rule_basedとの違い:
    - 明確な状態遷移で管理
    - 状態ごとにタイマーを持つ
    - センサーパターンマッチングで判断
    """
    
    STATE_NAMES = {
        State.INIT: "初期化",
        State.WALL_FOLLOW: "壁沿い",
        State.LEFT_TURN: "左旋回",
        State.RIGHT_TURN: "右旋回",
        State.EMERGENCY: "緊急",
        State.RECOVER: "復帰",
        State.STOPPED: "停止",
    }
    
    def __init__(self):
        self.state = State.INIT
        self.prev_state = State.INIT
        self.state_start_time = time.monotonic()
        self.state_duration = 0.0
        
        # 出力値
        self.steering = SERVO_CENTER
        self.throttle = THROTTLE_STOP
        
        # 壁沿い走行用
        self.last_left_distance = TARGET_LEFT_DISTANCE
    
    def update(self, sensor_data):
        """
        センサーデータから状態を更新し、制御値を決定
        
        Args:
            sensor_data: SensorDataオブジェクト
        
        Returns:
            tuple: (steering, throttle)
        """
        now = time.monotonic()
        self.state_duration = now - self.state_start_time
        
        # センサー値を取得（無効値は大きな値に）
        L = sensor_data.left if sensor_data.left < SENSOR_INVALID_VALUE else 2000
        FL = sensor_data.front_left if sensor_data.front_left < SENSOR_INVALID_VALUE else 2000
        C = sensor_data.center if sensor_data.center < SENSOR_INVALID_VALUE else 2000
        FR = sensor_data.front_right if sensor_data.front_right < SENSOR_INVALID_VALUE else 2000
        R = sensor_data.right if sensor_data.right < SENSOR_INVALID_VALUE else 2000
        
        # センサーパターンを解析
        pattern = self._detect_pattern(L, FL, C, FR, R)
        
        # 現在の状態に応じた処理
        next_state = self.state
        
        if self.state == State.INIT:
            next_state = State.WALL_FOLLOW
            
        elif self.state == State.WALL_FOLLOW:
            next_state, self.steering, self.throttle = self._handle_wall_follow(L, FL, C, FR, R, pattern)
            
        elif self.state == State.LEFT_TURN:
            next_state, self.steering, self.throttle = self._handle_left_turn(L, FL, C, FR, R, pattern)
            
        elif self.state == State.RIGHT_TURN:
            next_state, self.steering, self.throttle = self._handle_right_turn(L, FL, C, FR, R, pattern)
            
        elif self.state == State.EMERGENCY:
            next_state, self.steering, self.throttle = self._handle_emergency(L, FL, C, FR, R, pattern)
            
        elif self.state == State.RECOVER:
            next_state, self.steering, self.throttle = self._handle_recover(L, FL, C, FR, R, pattern)
        
        # 状態遷移
        if next_state != self.state:
            self._transition_to(next_state)
        
        self.last_left_distance = L
        return self.steering, self.throttle
    
    def _detect_pattern(self, L, FL, C, FR, R):
        """センサーパターンを検出"""
        
        # S字区間の検出（両側に壁が近い）
        is_s_curve = (L < S_CURVE_DETECTION_THRESHOLD and R < S_CURVE_DETECTION_THRESHOLD)
        
        # 右壁の方が近い場合は右S字（左に回避）
        # 左壁の方が近い場合は左S字（右に回避）
        right_s_curve = is_s_curve and (R < L - 100)  # 右が100mm以上近い
        left_s_curve = is_s_curve and (L < R - 100)   # 左が100mm以上近い
        
        return {
            'front_very_close': C < WALL_VERY_CLOSE,
            'front_blocked': C < FRONT_BLOCKED_THRESHOLD,
            'left_wall_exists': L < WALL_NONE,
            'left_wall_close': L < WALL_CLOSE,
            'left_corner_detected': L > LEFT_CORNER_OPEN_THRESHOLD and C < FRONT_BLOCKED_THRESHOLD,
            'right_wall_close': R < RIGHT_WALL_CLOSE_THRESHOLD,
            'is_s_curve': is_s_curve,
            'right_s_curve': right_s_curve,
            'left_s_curve': left_s_curve,
        }
    
    def _handle_wall_follow(self, L, FL, C, FR, R, pattern):
        """壁沿い走行状態の処理"""
        
        # 緊急回避（正面が非常に近い）
        if pattern['front_very_close']:
            return State.EMERGENCY, SERVO_RIGHT, THROTTLE_STOP
        
        # S字カーブの右折（左壁が近いS字）
        if pattern['left_s_curve']:
            return State.RIGHT_TURN, SERVO_RIGHT, THROTTLE_SLOW
        
        # 左コーナー検出（左が大きく開けた & 正面に壁）
        if pattern['left_corner_detected']:
            return State.LEFT_TURN, SERVO_LEFT, THROTTLE_SLOW
        
        # 右コーナー検出（正面が近い & 左壁あり）
        # 右壁の距離条件(R > WALL_FAR)を削除し、狭い場所でも右折できるようにする
        if C < FRONT_BLOCKED_THRESHOLD and L < WALL_FAR:
            return State.RIGHT_TURN, SERVO_RIGHT, THROTTLE_SLOW
        
        # PID制御で壁沿い走行
        error = L - TARGET_LEFT_DISTANCE
        
        # 左前が近すぎる場合は、壁に寄りすぎているので右に修正
        if FL < TARGET_LEFT_DISTANCE * 1.5:  # 150mm未満
             # 左前が近い → 右へ避ける (強制的にターゲットを大きく見せる、またはステアリングを右へ)
             steering = SERVO_CENTER + 20  # 右へ
             error = 999 # 加速させないために大きな誤差にしておく
        else:
            steering = SERVO_CENTER - (error * 0.15)  # ゲインを戻す（0.1→0.15）
        
        steering = max(SERVO_LEFT, min(SERVO_RIGHT, steering))
        
        # 速度調整（左壁が近すぎたら減速）
        if L < WALL_CLOSE:
            throttle = THROTTLE_SLOW
        elif abs(error) < 100:  # 誤差が小さければ加速
            throttle = THROTTLE_NORMAL
        else:
            throttle = THROTTLE_SLOW
        
        return State.WALL_FOLLOW, steering, throttle
    
    def _handle_left_turn(self, L, FL, C, FR, R, pattern):
        """左コーナー状態の処理"""
        
        # 緊急回避
        if pattern['front_very_close']:
            return State.EMERGENCY, SERVO_CENTER, THROTTLE_STOP
        
        # 最小旋回時間は維持（0.5秒）
        if self.state_duration < TURN_MIN_DURATION:
            return State.LEFT_TURN, SERVO_LEFT, THROTTLE_SLOW
        
        # タイムアウト
        if self.state_duration > TURN_MAX_DURATION:
            return State.WALL_FOLLOW, SERVO_CENTER, THROTTLE_SLOW
        
        # 左壁が見つかり、前方が開けたら壁沿いに戻る
        if L < WALL_FAR and C > FRONT_BLOCKED_THRESHOLD:
            return State.WALL_FOLLOW, SERVO_SLIGHT_LEFT, THROTTLE_SLOW
        
        # 継続して左旋回
        return State.LEFT_TURN, SERVO_LEFT, THROTTLE_SLOW
    
    def _handle_right_turn(self, L, FL, C, FR, R, pattern):
        """右コーナー状態の処理（できるだけ使わない）"""
        
        # 緊急回避
        if pattern['front_very_close']:
            return State.EMERGENCY, SERVO_RIGHT, THROTTLE_STOP  # 右のまま停止
        
        # 最小旋回時間は維持
        if self.state_duration < TURN_MIN_DURATION:
            return State.RIGHT_TURN, SERVO_RIGHT, THROTTLE_SLOW
        
        # タイムアウト
        if self.state_duration > TURN_MAX_DURATION:
            return State.WALL_FOLLOW, SERVO_CENTER, THROTTLE_SLOW
        
        # 前方が開けたら壁沿いに戻る
        if C > FRONT_BLOCKED_THRESHOLD * 1.5:  # 1.2→1.5に変更
            return State.WALL_FOLLOW, SERVO_CENTER, THROTTLE_SLOW
        
        # 継続して右旋回
        return State.RIGHT_TURN, SERVO_RIGHT, THROTTLE_SLOW
    
    def _handle_emergency(self, L, FL, C, FR, R, pattern):
        """緊急回避状態の処理"""
        
        # 最小停止時間（0.3秒）
        if self.state_duration < 0.3:
            return State.EMERGENCY, SERVO_CENTER, THROTTLE_STOP
        
        # 回避方向の判定
        if pattern['right_s_curve']:
            # 右S字 → 左に回避
            avoid_direction = SERVO_LEFT
        elif pattern['left_s_curve']:
            # 左S字 → 右に回避
            avoid_direction = SERVO_RIGHT
        else:
            # 通常区間 → 左に回避（左手法）
            avoid_direction = SERVO_LEFT
        
        # 前方が開けたら次の状態へ
        if C > WALL_VERY_CLOSE * 2:  # 300mm以上
            if L > WALL_NONE:
                return State.LEFT_TURN, SERVO_LEFT, THROTTLE_SLOW
            else:
                return State.WALL_FOLLOW, SERVO_CENTER, THROTTLE_SLOW
        
        # まだ近ければ後退（回避方向にハンドルを切る）
        return State.RECOVER, avoid_direction, THROTTLE_STOP
    
    def _handle_recover(self, L, FL, C, FR, R, pattern):
        """復帰状態の処理"""
        
        # 回避方向の判定（EMERGENCYと同じロジック）
        if pattern['right_s_curve']:
            avoid_direction = SERVO_LEFT
        elif pattern['left_s_curve']:
            avoid_direction = SERVO_RIGHT
        else:
            avoid_direction = SERVO_LEFT
        
        # 最小後退時間（0.5秒）
        if self.state_duration < 0.5:
            return State.RECOVER, avoid_direction, THROTTLE_REVERSE
        
        # 十分離れたら壁沿いに戻る
        if C > WALL_MEDIUM:
            return State.WALL_FOLLOW, SERVO_CENTER, THROTTLE_SLOW
        
        # まだ近ければ継続
        return State.RECOVER, avoid_direction, THROTTLE_REVERSE
    
    def _transition_to(self, new_state):
        """状態遷移"""
        if LOG_STATE_CHANGES:
            old_name = self.STATE_NAMES.get(self.state, "?")
            new_name = self.STATE_NAMES.get(new_state, "?")
            print(f"  状態遷移: {old_name} -> {new_name}")
        
        self.prev_state = self.state
        self.state = new_state
        self.state_start_time = time.monotonic()
        self.state_duration = 0.0
    
    def get_state_name(self):
        """現在の状態名を取得"""
        return self.STATE_NAMES.get(self.state, "不明")
    
    def format_debug(self, sensor_data):
        """デバッグ情報を整形"""
        # デバッグ表示用にもパターンを計算
        L = sensor_data.left if sensor_data.left < SENSOR_INVALID_VALUE else 2000
        FL = sensor_data.front_left if sensor_data.front_left < SENSOR_INVALID_VALUE else 2000
        C = sensor_data.center if sensor_data.center < SENSOR_INVALID_VALUE else 2000
        FR = sensor_data.front_right if sensor_data.front_right < SENSOR_INVALID_VALUE else 2000
        R = sensor_data.right if sensor_data.right < SENSOR_INVALID_VALUE else 2000
        
        pattern = self._detect_pattern(L, FL, C, FR, R)
        flags = []
        if pattern['left_s_curve']: flags.append("L-S")
        if pattern['right_s_curve']: flags.append("R-S")
        if pattern['front_blocked']: flags.append("BLK")
        if pattern['front_very_close']: flags.append("CRT")
        
        flag_str = ",".join(flags) if flags else "-"
        
        return (
            f"[{self.get_state_name():4}] "
            f"{sensor_data} | "
            f"St:{self.steering:5.1f} Th:{self.throttle:+.2f} "
            f"({self.state_duration:.1f}s) "
            f"[{flag_str}]"
        )
