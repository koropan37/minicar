"""
モーター制御モジュール（PCA9685）
"""

import board
import busio
from adafruit_pca9685 import PCA9685
from adafruit_motor import servo


class MLMotorController:
    """モーター制御（PCA9685）"""
    
    def __init__(self):
        # 設定は外部から受け取る（settings.pyから）
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.pca = None
        self.steering_servo = None
        self.esc = None
    
    def initialize(self, pca_address=0x40, pca_freq=50,
                   servo_channel=0, servo_min_pulse=500, servo_max_pulse=2500,
                   esc_channel=1, esc_min_pulse=1000, esc_max_pulse=2000,
                   servo_center=114):
        """
        初期化
        
        Args:
            pca_address: PCA9685のI2Cアドレス
            pca_freq: PWM周波数
            servo_channel: サーボのチャンネル
            servo_min_pulse: サーボの最小パルス幅
            servo_max_pulse: サーボの最大パルス幅
            esc_channel: ESCのチャンネル
            esc_min_pulse: ESCの最小パルス幅
            esc_max_pulse: ESCの最大パルス幅
            servo_center: サーボの中央角度
        """
        print("モーター初期化中...")
        
        self.pca = PCA9685(self.i2c, address=pca_address)
        self.pca.frequency = pca_freq
        
        # ステアリングサーボ
        self.steering_servo = servo.Servo(
            self.pca.channels[servo_channel],
            min_pulse=servo_min_pulse,
            max_pulse=servo_max_pulse
        )
        
        # ESC
        self.esc = servo.ContinuousServo(
            self.pca.channels[esc_channel],
            min_pulse=esc_min_pulse,
            max_pulse=esc_max_pulse
        )
        
        # 初期位置
        self.steering_servo.angle = servo_center
        self.esc.throttle = 0.0
        
        print("✓ モーター初期化完了")
    
    def drive(self, servo_angle, throttle):
        """駆動"""
        self.steering_servo.angle = servo_angle
        self.esc.throttle = throttle
    
    def stop(self, servo_center=114):
        """停止"""
        self.esc.throttle = 0.0
        self.steering_servo.angle = servo_center
    
    def cleanup(self):
        """クリーンアップ"""
        self.stop()
        self.pca.deinit()