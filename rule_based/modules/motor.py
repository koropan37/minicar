"""
モーター制御モジュール (PCA9685 + サーボ/ESC)
ステアリングとスロットルを制御
"""

import board
import time
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo

from config.settings import (
    PCA9685_FREQUENCY,
    SERVO_CHANNEL, SERVO_MIN_PULSE, SERVO_MAX_PULSE,
    SERVO_CENTER, SERVO_LEFT, SERVO_RIGHT,
    ESC_CHANNEL, ESC_MIN_PULSE, ESC_MAX_PULSE,
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
        self.esc_channel = None
        
    def initialize(self):
        """
        モーター/サーボの初期化処理
        
        Returns:
            bool: 初期化成功時True
        """
        print("モーターコントローラー初期化開始...")
        
        # PCA9685の設定
        self.pca = PCA9685(self.i2c)
        self.pca.frequency = PCA9685_FREQUENCY
        
        # サーボ設定（ステアリング）
        self.steering_servo = servo.Servo(
            self.pca.channels[SERVO_CHANNEL],
            min_pulse=SERVO_MIN_PULSE,
            max_pulse=SERVO_MAX_PULSE
        )
        
        # ESC設定（モーター）- duty_cycleで直接制御
        self.esc_channel = self.pca.channels[ESC_CHANNEL]
        
        # 初期位置に設定
        self.set_steering_angle(SERVO_CENTER)
        self.set_throttle(THROTTLE_NEUTRAL)
        time.sleep(0.5)
        
        print(f"  ステアリング: 左={SERVO_LEFT}° 中央={SERVO_CENTER}° 右={SERVO_RIGHT}°")
        print(f"  ESCパルス: {ESC_MIN_PULSE}us ~ {ESC_MAX_PULSE}us")
        print("モーターコントローラー初期化完了")
        return True
    
    def set_steering_angle(self, angle):
        """
        ステアリング角度を直接設定
        
        Args:
            angle: サーボ角度 (SERVO_LEFT ~ SERVO_RIGHT)
        
        Returns:
            float: 実際に設定された角度
        """
        # 範囲制限
        angle = max(SERVO_LEFT, min(SERVO_RIGHT, angle))
        self.steering_servo.angle = angle
        return angle
    
    def set_steering_normalized(self, value):
        """
        正規化された値でステアリングを設定
        
        Args:
            value: -1.0（左）〜 1.0（右）の値
        
        Returns:
            float: 実際に設定された角度
        """
        if value >= 0:
            angle = SERVO_CENTER + (value * (SERVO_RIGHT - SERVO_CENTER))
        else:
            angle = SERVO_CENTER + (value * (SERVO_CENTER - SERVO_LEFT))
        
        return self.set_steering_angle(angle)
    
    def set_throttle(self, value):
        """
        スロットルを設定（ContinuousServo互換の-1.0~1.0形式）
        
        Args:
            value: -1.0（後退最大）〜 0.0（停止）〜 1.0（前進最大）
        
        Returns:
            float: 設定した値
        """
        # ESCのニュートラルは中間パルス幅
        neutral_pulse = (ESC_MIN_PULSE + ESC_MAX_PULSE) / 2  # 1550us
        
        if value > 0:  # 前進
            pulse_us = neutral_pulse + (value * (ESC_MAX_PULSE - neutral_pulse))
        elif value < 0:  # 後退
            pulse_us = neutral_pulse + (value * (neutral_pulse - ESC_MIN_PULSE))
        else:  # 停止
            pulse_us = neutral_pulse
        
        # パルス幅を範囲内にクリップ
        pulse_us = max(ESC_MIN_PULSE, min(ESC_MAX_PULSE, pulse_us))
        
        # Duty Cycle計算 (16-bit: 0-65535)
        # duty_cycle = (pulse_us / 周期us) * 65535
        period_us = 1000000 / PCA9685_FREQUENCY  # 50Hz = 20000us
        duty = int((pulse_us / period_us) * 65535)
        self.esc_channel.duty_cycle = duty
        
        return value
    
    def stop(self):
        """緊急停止（モーター停止 + ステアリング中央）"""
        self.set_throttle(THROTTLE_NEUTRAL)
        self.set_steering_angle(SERVO_CENTER)
    
    def cleanup(self):
        """モーターコントローラーのクリーンアップ"""
        self.stop()
        if self.pca:
            self.pca.deinit()
        print("モーターコントローラーをクリーンアップしました")
