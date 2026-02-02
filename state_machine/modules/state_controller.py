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
    LOG_STATE_CHANGES
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
        pattern = self._analyze_pattern(L, FL, C, FR, R)
        
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
    
    def _analyze_pattern(self, L, FL, C, FR, R):
        """
        センサー値からパターンを解析
        
        Returns:
            dict: 各種フラグ
        """
        return {
            'front_blocked': C < FRONT_BLOCKED_THRESHOLD or FL < FRONT_BLOCKED_THRESHOLD * 0.8,
            'front_very_close': C < WALL_VERY_CLOSE,
            'left_open': L > LEFT_CORNER_OPEN_THRESHOLD and FL > LEFT_CORNER_OPEN_THRESHOLD,
            'left_close': L < WALL_CLOSE,
            'left_very_close': L < WALL_VERY_CLOSE or FL < WALL_VERY_CLOSE,
            'right_close': R < RIGHT_WALL_CLOSE_THRESHOLD or FR < RIGHT_WALL_CLOSE_THRESHOLD,
            'right_very_close': R < WALL_VERY_CLOSE or FR < WALL_VERY_CLOSE,
            'corridor': L < WALL_FAR and R < WALL_FAR,  # 両側に壁（廊下）
        }
    
    def _handle_wall_follow(self, L, FL, C, FR, R, pattern):
        """壁沿い走行状態の処理"""
        
        # 緊急回避チェック
        if pattern['front_very_close'] or pattern['left_very_close']:
            return State.EMERGENCY, SERVO_RIGHT, THROTTLE_STOP
        
        if pattern['right_very_close']:
            return State.EMERGENCY, SERVO_LEFT, THROTTLE_STOP
        
        # 右コーナー検出（前方が塞がれている）
        if pattern['front_blocked']:
            return State.RIGHT_TURN, SERVO_RIGHT, THROTTLE_SLOW
        
        # 左コーナー検出（左壁がなくなった）
        if pattern['left_open']:
            return State.LEFT_TURN, SERVO_LEFT, THROTTLE_SLOW
        
        # 通常の壁沿い走行
        steering, throttle = self._calculate_wall_follow(L, FL, C, pattern)
        return State.WALL_FOLLOW, steering, throttle
    
    def _calculate_wall_follow(self, L, FL, C, pattern):
        """壁沿い走行のステアリング計算"""
        
        # 左壁との距離誤差
        error = TARGET_LEFT_DISTANCE - L
        
        # 斜め左前センサーで補正（壁に向かっているかチェック）
        if FL < L * 0.85:
            # 壁に向かっている → より強く右へ
            error += (L - FL) * 0.5
        
        # ステアリング計算（簡易比例制御）
        # 壁に近い(error > 0) → 右へ(角度大)
        # 壁から遠い(error < 0) → 左へ(角度小)
        correction = error * 0.15
        steering = SERVO_CENTER + correction
        steering = max(SERVO_LEFT, min(SERVO_RIGHT, steering))
        
        # 速度決定
        if abs(error) < WALL_FOLLOW_TOLERANCE and C > WALL_FAR:
            throttle = THROTTLE_FAST  # 安定していて前方開けている
        elif abs(error) < WALL_FOLLOW_TOLERANCE * 2:
            throttle = THROTTLE_NORMAL
        else:
            throttle = THROTTLE_SLOW
        
        return steering, throttle
    
    def _handle_left_turn(self, L, FL, C, FR, R, pattern):
        """左コーナー状態の処理"""
        
        # 緊急回避
        if pattern['front_very_close']:
            return State.EMERGENCY, SERVO_RIGHT, THROTTLE_STOP
        
        # 最小旋回時間は維持
        if self.state_duration < TURN_MIN_DURATION:
            return State.LEFT_TURN, SERVO_LEFT, THROTTLE_SLOW
        
        # タイムアウト
        if self.state_duration > TURN_MAX_DURATION:
            return State.WALL_FOLLOW, SERVO_CENTER, THROTTLE_SLOW
        
        # 左壁が見つかったら壁沿いに戻る（条件を緩和）
        # 変更前: L < WALL_FAR and FL < WALL_FAR
        # 変更後: L < WALL_NONE and FL < WALL_NONE （より早く壁沿いに戻る）
        if L < WALL_NONE or FL < WALL_NONE:
            return State.WALL_FOLLOW, SERVO_SLIGHT_LEFT, THROTTLE_SLOW
        
        # 継続して左旋回
        return State.LEFT_TURN, SERVO_LEFT, THROTTLE_SLOW
    
    def _handle_right_turn(self, L, FL, C, FR, R, pattern):
        """右コーナー状態の処理"""
        
        # 緊急回避（正面が非常に近い）
        if pattern['front_very_close']:
            return State.EMERGENCY, SERVO_RIGHT, THROTTLE_STOP
        
        # 最小旋回時間は維持
        if self.state_duration < TURN_MIN_DURATION:
            return State.RIGHT_TURN, SERVO_RIGHT, THROTTLE_SLOW
        
        # タイムアウト
        if self.state_duration > TURN_MAX_DURATION:
            return State.RECOVER, SERVO_CENTER, THROTTLE_REVERSE
        
        # 前方が開けたら壁沿いに戻る
        if C > FRONT_BLOCKED_THRESHOLD * 1.2 and FL > FRONT_BLOCKED_THRESHOLD:
            return State.WALL_FOLLOW, SERVO_SLIGHT_RIGHT, THROTTLE_SLOW
        
        # 継続して右旋回
        return State.RIGHT_TURN, SERVO_RIGHT, THROTTLE_SLOW
    
    def _handle_emergency(self, L, FL, C, FR, R, pattern):
        """緊急回避状態の処理"""
        
        # 少し待ってから判断
        if self.state_duration < 0.2:
            # 左が近ければ右へ、右が近ければ左へ
            if pattern['left_very_close']:
                return State.EMERGENCY, SERVO_RIGHT, THROTTLE_STOP
            elif pattern['right_very_close']:
                return State.EMERGENCY, SERVO_LEFT, THROTTLE_STOP
            else:
                return State.EMERGENCY, SERVO_CENTER, THROTTLE_STOP
        
        # 状況が改善したら復帰
        if not pattern['front_very_close'] and not pattern['left_very_close'] and not pattern['right_very_close']:
            return State.WALL_FOLLOW, SERVO_CENTER, THROTTLE_SLOW
        
        # まだ危険なら後退
        if self.state_duration > 0.5:
            return State.RECOVER, SERVO_CENTER, THROTTLE_REVERSE
        
        return State.EMERGENCY, self.steering, THROTTLE_STOP
    
    def _handle_recover(self, L, FL, C, FR, R, pattern):
        """リカバリー状態の処理"""
        
        # 後退時間
        if self.state_duration < 0.5:
            return State.RECOVER, SERVO_CENTER, THROTTLE_REVERSE
        
        # 状況確認して壁沿いに戻る
        if C > WALL_CLOSE and not pattern['left_very_close']:
            return State.WALL_FOLLOW, SERVO_CENTER, THROTTLE_SLOW
        
        # まだダメならもう少し後退
        if self.state_duration < 1.5:
            return State.RECOVER, SERVO_CENTER, THROTTLE_REVERSE
        
        # タイムアウト → とりあえず壁沿いに戻す
        return State.WALL_FOLLOW, SERVO_CENTER, THROTTLE_SLOW
    
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
        return (
            f"[{self.get_state_name():4}] "
            f"{sensor_data} | "
            f"St:{self.steering:5.1f} Th:{self.throttle:+.2f} "
            f"({self.state_duration:.1f}s)"
        )
