"""
モーター制御モジュール (PCA9685 + サーボ/ESC)
test_sensor.py の設定を参考に作成
"""

import board
import time
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo

import sys
sys.path.append('..')
from config.settings import (
    PCA9685_FREQUENCY,
    SERVO_CHANNEL, SERVO_MIN_PULSE, SERVO_MAX_PULSE,
    SERVO_CENTER, SERVO_LEFT, SERVO_RIGHT,
    ESC_CHANNEL, ESC_MIN_PULSE, ESC_MAX_PULSE,
    THROTTLE_FORWARD_MIN, THROTTLE_FORWARD_MAX,
    THROTTLE_BACKWARD_MIN, THROTTLE_BACKWARD_MAX,
    THROTTLE_NEUTRAL
)


class MotorController:
    """モーター制御クラス（ステアリング + スロットル）"""
    
    def __init__(self, i2c=None):
        """
        モーターコントローラーの初期化
        
        Args:
            i2c: I2Cバスインスタンス（Noneの場合は自動作成）
        """
        self.i2c = i2c if i2c else board.I2C()
        self.pca = None
        self.steering_servo = None
        self.motor_esc = None
        
    def initialize(self):
        """モーター/サーボの初期化処理"""
        # PCA9685の設定
        self.pca = PCA9685(self.i2c)
        self.pca.frequency = PCA9685_FREQUENCY
        
        # サーボ設定（ステアリング）
        self.steering_servo = servo.Servo(
            self.pca.channels[SERVO_CHANNEL],
            min_pulse=SERVO_MIN_PULSE,
            max_pulse=SERVO_MAX_PULSE
        )
        
        # ESC設定（モーター）
        self.motor_esc = servo.ContinuousServo(
            self.pca.channels[ESC_CHANNEL],
            min_pulse=ESC_MIN_PULSE,
            max_pulse=ESC_MAX_PULSE
        )
        
        # 初期位置に設定
        self.steering_servo.angle = SERVO_CENTER
        self.motor_esc.throttle = THROTTLE_NEUTRAL
        time.sleep(0.5)
        
        print("モーターコントローラーが初期化されました")
        print(f"  前進スロットル範囲: {THROTTLE_FORWARD_MIN} 〜 {THROTTLE_FORWARD_MAX}")
        return True
    
    def set_steering(self, value):
        """
        ステアリングを設定
        
        Args:
            value: -1.0（左）〜 1.0（右）の値
        """
        # -1.0〜1.0 を SERVO_LEFT〜SERVO_RIGHT に変換
        # value = -1.0 → SERVO_LEFT (92)
        # value = 0.0  → SERVO_CENTER (114)
        # value = 1.0  → SERVO_RIGHT (140)
        
        if value >= 0:
            angle = SERVO_CENTER + (value * (SERVO_RIGHT - SERVO_CENTER))
        else:
            angle = SERVO_CENTER + (value * (SERVO_CENTER - SERVO_LEFT))
        
        # 範囲制限
        angle = max(SERVO_LEFT, min(SERVO_RIGHT, angle))
        self.steering_servo.angle = angle
        
        return angle
    
    def set_throttle(self, value):
        """
        スロットルを設定（トリガー押し込み具合で可変）
        
        Args:
            value: -1.0（後退全開）〜 1.0（前進全開）の値
            value == 0 の場合は停止
            
        前進時: 軽く押し→0.23, 全押し→0.50
        後退時: 軽く押し→-0.13, 全押し→-0.25
        停止時: 0.0
        """
        if value > 0:
            # 前進: 0.0〜1.0 を THROTTLE_FORWARD_MIN〜THROTTLE_FORWARD_MAX に変換
            throttle = THROTTLE_FORWARD_MIN + (value * (THROTTLE_FORWARD_MAX - THROTTLE_FORWARD_MIN))
        elif value < 0:
            # 後退: -1.0〜0.0 を THROTTLE_BACKWARD_MAX〜THROTTLE_BACKWARD_MIN に変換
            throttle = THROTTLE_BACKWARD_MIN + (abs(value) * (THROTTLE_BACKWARD_MAX - THROTTLE_BACKWARD_MIN))
        else:
            # 何も押していない → 停止
            throttle = THROTTLE_NEUTRAL
        
        self.motor_esc.throttle = throttle
        
        return throttle
    
    def stop(self):
        """緊急停止"""
        self.motor_esc.throttle = THROTTLE_NEUTRAL
        self.steering_servo.angle = SERVO_CENTER
        print("緊急停止しました")
    
    def cleanup(self):
        """モーターコントローラーのクリーンアップ"""
        self.stop()
        if self.pca:
            self.pca.deinit()
        print("モーターコントローラーをクリーンアップしました")
