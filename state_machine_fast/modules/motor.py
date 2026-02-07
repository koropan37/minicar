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
    THROTTLE_STOP
)


class MotorController:
    """モーター制御クラス"""
    
    def __init__(self, i2c=None):
        self.i2c = i2c if i2c else board.I2C()
        self.pca = None
        self.steering_servo = None
        self.esc_channel = None
        self._current_steering = SERVO_CENTER
        self._current_throttle = THROTTLE_STOP
        
    def initialize(self):
        """モーター/サーボの初期化"""
        print("モーターコントローラー初期化開始...")
        
        self.pca = PCA9685(self.i2c)
        self.pca.frequency = PCA9685_FREQUENCY
        
        # サーボ設定（ステアリング）
        self.steering_servo = servo.Servo(
            self.pca.channels[SERVO_CHANNEL],
            min_pulse=SERVO_MIN_PULSE,
            max_pulse=SERVO_MAX_PULSE
        )
        
        # ESC設定（モーター）
        self.esc_channel = self.pca.channels[ESC_CHANNEL]
        
        # 初期位置
        self.steer(SERVO_CENTER)
        self.throttle(THROTTLE_STOP)
        time.sleep(0.5)
        
        print(f"  ステアリング: {SERVO_LEFT}° ~ {SERVO_CENTER}° ~ {SERVO_RIGHT}°")
        print("モーターコントローラー初期化完了")
        return True
    
    def steer(self, angle):
        """
        ステアリング角度を設定
        
        Args:
            angle: サーボ角度 (SERVO_LEFT ~ SERVO_RIGHT)
        """
        angle = max(SERVO_LEFT, min(SERVO_RIGHT, angle))
        self.steering_servo.angle = angle
        self._current_steering = angle
        return angle
    
    def throttle(self, value):
        """
        スロットルを設定
        
        Args:
            value: -1.0（後退）〜 0.0（停止）〜 1.0（前進）
        """
        neutral_pulse = (ESC_MIN_PULSE + ESC_MAX_PULSE) / 2
        
        if value > 0:
            pulse_us = neutral_pulse + (value * (ESC_MAX_PULSE - neutral_pulse))
        elif value < 0:
            pulse_us = neutral_pulse + (value * (neutral_pulse - ESC_MIN_PULSE))
        else:
            pulse_us = neutral_pulse
        
        pulse_us = max(ESC_MIN_PULSE, min(ESC_MAX_PULSE, pulse_us))
        
        period_us = 1000000 / PCA9685_FREQUENCY
        duty = int((pulse_us / period_us) * 65535)
        self.esc_channel.duty_cycle = duty
        self._current_throttle = value
        return value
    
    def drive(self, steering, throttle_value):
        """
        ステアリングとスロットルを同時に設定
        
        Args:
            steering: ステアリング角度
            throttle_value: スロットル値
        """
        self.steer(steering)
        self.throttle(throttle_value)
    
    def stop(self):
        """緊急停止"""
        self.throttle(THROTTLE_STOP)
        self.steer(SERVO_CENTER)
    
    @property
    def current_steering(self):
        return self._current_steering
    
    @property
    def current_throttle(self):
        return self._current_throttle
    
    def cleanup(self):
        """クリーンアップ"""
        self.stop()
        if self.pca:
            self.pca.deinit()
        print("モーターコントローラーをクリーンアップしました")
