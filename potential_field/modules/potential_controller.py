"""
仮想ポテンシャル法コントローラー
障害物からの反発力を計算して走行する
"""

import math

from config.settings import (
    SERVO_CENTER, SERVO_LEFT, SERVO_RIGHT,
    THROTTLE_STOP, THROTTLE_SLOW, THROTTLE_NORMAL, THROTTLE_REVERSE,
    WEIGHT_LEFT, WEIGHT_FRONT_LEFT, WEIGHT_FRONT, WEIGHT_FRONT_RIGHT, WEIGHT_RIGHT,
    POTENTIAL_STEER_GAIN, POTENTIAL_THROTTLE_BASE, POTENTIAL_THROTTLE_MIN,
    BRAKE_WEIGHT_FRONT, BRAKE_WEIGHT_SIDE_FRONT,
    EMERGENCY_DIST, SENSOR_INVALID_VALUE
)


class PotentialController:
    """
    仮想ポテンシャル法コントローラー
    各センサーの値を「反発力」として加算し、進行方向と速度を決定する
    """
    
    def __init__(self):
        self.steering = SERVO_CENTER
        self.throttle = THROTTLE_STOP
        self.total_force_x = 0.0 # 左右方向の力（正:右, 負:左）
        self.brake_force = 0.0   # 制動力
        
    def _calc_repulsive_force(self, distance, weight):
        """反発力を計算 F = w / d^2"""
        # 距離が0や極端に近い場合の保護
        dist_cm = max(distance, 50.0) / 10.0 # mm -> cm 単位で計算（値が大きくなりすぎないように）
        force = weight / (dist_cm * dist_cm)
        return force

    def update(self, sensor_data):
        """
        センサーデータから制御値を計算
        """
        # 無効値は無視するため非常に遠い距離とする
        L = sensor_data.left if sensor_data.left < SENSOR_INVALID_VALUE else 3000
        FL = sensor_data.front_left if sensor_data.front_left < SENSOR_INVALID_VALUE else 3000
        C = sensor_data.center if sensor_data.center < SENSOR_INVALID_VALUE else 3000
        FR = sensor_data.front_right if sensor_data.front_right < SENSOR_INVALID_VALUE else 3000
        R = sensor_data.right if sensor_data.right < SENSOR_INVALID_VALUE else 3000
        
        # 緊急停止判定（近すぎる場合）
        min_dist = min(L, FL, C, FR, R)
        if min_dist < EMERGENCY_DIST:
            self.throttle = THROTTLE_REVERSE
            self.steering = SERVO_CENTER # バック時はまっすぐ
            return self.steering, self.throttle
            
        # 1. ステアリング制御用の力計算 (横方向成分のみ簡易計算)
        # 左側センサー -> 右へ切る力 (+)
        force_L = self._calc_repulsive_force(L, WEIGHT_LEFT)
        force_FL = self._calc_repulsive_force(FL, WEIGHT_FRONT_LEFT)
        
        # 右側センサー -> 左へ切る力 (-)
        force_R = self._calc_repulsive_force(R, WEIGHT_RIGHT)
        force_FR = self._calc_repulsive_force(FR, WEIGHT_FRONT_RIGHT)
        
        # 正面は左右に障害物がある場合にバランスを取る役割
        # ここでは簡易的に左右の差分として計算
        
        # 合力
        # 左からの力 - 右からの力
        # 正の値 -> 右へ行け
        # 負の値 -> 左へ行け
        self.total_force_x = (force_L + force_FL) - (force_R + force_FR)
        
        # 操舵角への変換
        # ステアリングは値が大きいほど右、小さいほど左
        # Center + gain * force
        # forceが正(右へ行け) -> steeringを大きく
        delta_steer = self.total_force_x * POTENTIAL_STEER_GAIN
        self.steering = SERVO_CENTER + delta_steer
        
        # リミット
        self.steering = max(SERVO_LEFT, min(SERVO_RIGHT, self.steering))
        
        
        # 2. スロットル制御用の力計算 (ブレーキ力)
        # 前方の障害物が近いほど減速
        brake_C = self._calc_repulsive_force(C, BRAKE_WEIGHT_FRONT)
        brake_FL = self._calc_repulsive_force(FL, BRAKE_WEIGHT_SIDE_FRONT)
        brake_FR = self._calc_repulsive_force(FR, BRAKE_WEIGHT_SIDE_FRONT)
        
        self.brake_force = brake_C + brake_FL + brake_FR
        
        # 基本速度からブレーキ力を引く
        target_throttle = POTENTIAL_THROTTLE_BASE - (self.brake_force * 0.1) # 係数は調整必要
        
        # 最低速度リミット（止まらないように）
        self.throttle = max(POTENTIAL_THROTTLE_MIN, target_throttle)
        
        return self.steering, self.throttle
    
    def format_debug(self, sensor_data):
        """デバッグ表示"""
        return (
            f"[Potential] "
            f"{sensor_data} | "
            f"Fx:{self.total_force_x:+.2f} Brk:{self.brake_force:+.2f} "
            f"St:{self.steering:5.1f} Th:{self.throttle:+.2f}"
        )
