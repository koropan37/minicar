"""
ハイブリッド走行コントローラー
状況に応じて追従モードを切り替える

【完走優先版】
- 斜め前センサー(FL/FR)を活用した早期警戒機能を追加
- コーナー進入時の早期減速
"""

import time
from enum import Enum, auto

from config.settings import (
    SERVO_CENTER, SERVO_LEFT, SERVO_RIGHT,
    THROTTLE_STOP, THROTTLE_SLOW, THROTTLE_NORMAL, THROTTLE_REVERSE,
    WALL_TOO_CLOSE, WALL_VALID_MAX, FRONT_OBSTACLE_DIST,
    TARGET_WALL_DIST, STEERING_P_GAIN, CENTER_P_GAIN,
    SENSOR_INVALID_VALUE
)


class DriveMode(Enum):
    LEFT_FOLLOW = auto()   # 左壁追従
    RIGHT_FOLLOW = auto()  # 右壁追従
    CENTER_KEEP = auto()   # 中央維持
    FREE_ROAM = auto()     # 壁なし（直進/探索）
    AVOIDANCE = auto()     # 緊急回避/旋回
    RECOVERY = auto()      # バック
    CORNER_SLOW = auto()   # コーナー減速（斜め前センサー警戒時）


class HybridController:
    """
    ハイブリッド（適応型）走行制御
    左右のセンサー値を見て、最も安定して走れるモードを選択する
    """
    
    def __init__(self):
        self.mode = DriveMode.FREE_ROAM
        self.steering = SERVO_CENTER
        self.throttle = THROTTLE_STOP
        
    def update(self, sensor_data):
        """
        センサーデータから制御値を計算
        """
        # 無効値を大きな値に置換して扱いやすくする
        L = sensor_data.left if sensor_data.left < SENSOR_INVALID_VALUE else 2000
        FL = sensor_data.front_left if sensor_data.front_left < SENSOR_INVALID_VALUE else 2000
        C = sensor_data.center if sensor_data.center < SENSOR_INVALID_VALUE else 2000
        FR = sensor_data.front_right if sensor_data.front_right < SENSOR_INVALID_VALUE else 2000
        R = sensor_data.right if sensor_data.right < SENSOR_INVALID_VALUE else 2000
        
        # 壁の有効性判定
        left_valid = (L < WALL_VALID_MAX)
        right_valid = (R < WALL_VALID_MAX)
        front_blocked = (C < FRONT_OBSTACLE_DIST)

        # 斜め前センサーによる早期警戒（追加）
        DIAGONAL_WARNING = 350   # 斜め前がこれ以下なら警戒
        DIAGONAL_DANGER = 200    # 斜め前がこれ以下なら危険
        fl_danger = (FL < DIAGONAL_DANGER)
        fr_danger = (FR < DIAGONAL_DANGER)
        fl_warning = (FL < DIAGONAL_WARNING)
        fr_warning = (FR < DIAGONAL_WARNING)

        # モード決定と制御
        if C < WALL_TOO_CLOSE or L < 120 or R < 120 or (fl_danger and fr_danger):
            # 1. 極端に近い障害物 -> リカバリー（後退）
            self.mode = DriveMode.RECOVERY
            self.steering = SERVO_CENTER
            self.throttle = THROTTLE_REVERSE
            
        elif front_blocked or fl_danger or fr_danger:
            # 2. 前方or斜め前が塞がれている -> 広い方へ旋回 (Avoidance)
            self.mode = DriveMode.AVOIDANCE
            self.throttle = THROTTLE_SLOW
            
            # 左の方が広いなら左へ、右の方が広いなら右へ
            # ただし、壁沿い走行中なら壁と逆へ
            space_left = L + FL
            space_right = R + FR
            
            if space_left > space_right:
                self.steering = SERVO_LEFT
            else:
                self.steering = SERVO_RIGHT
                
        elif fl_warning or fr_warning:
            # 2.5 斜め前が警戒レベル -> コーナー減速
            self.mode = DriveMode.CORNER_SLOW
            self.throttle = THROTTLE_SLOW

            if fl_warning and not fr_warning:
                # 左斜め前が近い → 右へ
                self.steering = SERVO_CENTER + 10
            elif fr_warning and not fl_warning:
                # 右斜め前が近い → 左へ
                self.steering = SERVO_CENTER - 10
            else:
                # 両方警戒 → 広い方へ
                if FL > FR:
                    self.steering = SERVO_LEFT + 5
                else:
                    self.steering = SERVO_RIGHT - 5

        elif left_valid and right_valid:
            # 3. 両側に壁がある -> 中央維持 (Center Keep)
            self.mode = DriveMode.CENTER_KEEP
            self.throttle = THROTTLE_NORMAL
            
            # 左右差を0にする制御
            # error > 0 (左が遠い) -> 左へ切りたい
            # error < 0 (右が遠い) -> 右へ切りたい
            # ステアリング仕様: 小さい値=左, 大きい値=右
            # Center(114) - gain * error だと、error>0のとき値が小さくなり左へ切れる
            
            diff = L - R
            control = diff * CENTER_P_GAIN
            self.steering = SERVO_CENTER - control
            
        elif left_valid:
            # 4. 左壁のみ有効 -> 左壁追従 (Left Follow)
            self.mode = DriveMode.LEFT_FOLLOW
            self.throttle = THROTTLE_NORMAL
            
            error = L - TARGET_WALL_DIST
            # error > 0 (壁から遠い) -> 左へ寄せたい -> ステアリング値を減らす
            control = error * STEERING_P_GAIN
            self.steering = SERVO_CENTER - control
            
        elif right_valid:
            # 5. 右壁のみ有効 -> 右壁追従 (Right Follow)
            self.mode = DriveMode.RIGHT_FOLLOW
            self.throttle = THROTTLE_NORMAL
            
            error = R - TARGET_WALL_DIST
            # error > 0 (壁から遠い) -> 右へ寄せたい -> ステアリング値を増やす
            # しかしステアリング仕様は増やすと右。
            # 右壁から遠い(=Rが大きい)ときは右に切りたい。
            # 左壁から遠い(=Lが大きい)ときは左に切りたい。
            
            # 右壁の場合: Rが大きい -> 右(値大)にしたい -> Center + control
            control = error * STEERING_P_GAIN
            self.steering = SERVO_CENTER + control
            
        else:
            # 6. 壁が見つからない -> 直進探索 (Free Roam)
            self.mode = DriveMode.FREE_ROAM
            self.throttle = THROTTLE_NORMAL
            self.steering = SERVO_CENTER
            
        # ステアリングリミット
        self.steering = max(SERVO_LEFT, min(SERVO_RIGHT, self.steering))
        
        return self.steering, self.throttle
    
    def format_debug(self, sensor_data):
        """デバッグ表示"""
        return (
            f"[{self.mode.name:10}] "
            f"{sensor_data} | "
            f"St:{self.steering:5.1f} Th:{self.throttle:+.2f}"
        )
