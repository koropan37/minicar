"""
ハイブリッド走行コントローラー
状況に応じて追従モードを切り替える
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
        
        # モード決定と制御
        if C < WALL_TOO_CLOSE or L < 100 or R < 100:
            # 1. 極端に近い障害物 -> リカバリー（後退）
            self.mode = DriveMode.RECOVERY
            self.steering = SERVO_CENTER
            self.throttle = THROTTLE_REVERSE
            
        elif front_blocked:
            # 2. 前方が塞がれている -> 広い方へ旋回 (Avoidance)
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
