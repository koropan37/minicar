#!/usr/bin/env python3
"""
機械学習モデルを使った自動運転スクリプト
"""

import os
import sys
import time
import argparse

# プロジェクトルートをパスに追加
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.append(project_root)

from predict import MLPredictor
from modules import MLSensorManager, MLMotorController, DataLogger
from config import settings


class MLDriver:
    """機械学習による自動運転クラス"""

    def __init__(self, throttle=None, enable_logging=True):
        self.base_throttle = throttle if throttle is not None else settings.THROTTLE_NORMAL
        self.running = False

        self.predictor = None
        self.sensors = None
        self.motor = None
        self.logger = DataLogger(enabled=enable_logging)

        print("=" * 50)
        print("機械学習自動運転システム")
        print("=" * 50)
        print(f"スロットル: {self.base_throttle}")
        print(f"データログ: {'有効' if enable_logging else '無効'}")
    
    def initialize(self):
        """初期化"""
        print("\n--- 初期化開始 ---")
        
        print("\n[1/3] 機械学習モデル読み込み...")
        self.predictor = MLPredictor()
        
        print("\n[2/3] センサー初期化...")
        self.sensors = MLSensorManager()
        self.sensors.initialize(
            xshut_pins=settings.XSHUT_PINS,
            base_address=settings.SENSOR_BASE_ADDRESS,
            timing_budget=settings.SENSOR_TIMING_BUDGET,
            inter_measurement=settings.SENSOR_INTER_MEASUREMENT,
            invalid_value=settings.SENSOR_INVALID_VALUE
        )
        
        print("\n[3/3] モーター初期化...")
        self.motor = MLMotorController()
        self.motor.initialize(
            pca_address=settings.PCA9685_ADDRESS,
            pca_freq=settings.PCA9685_FREQUENCY,
            servo_channel=settings.SERVO_CHANNEL,
            servo_min_pulse=settings.SERVO_MIN_PULSE,
            servo_max_pulse=settings.SERVO_MAX_PULSE,
            esc_channel=settings.ESC_CHANNEL,
            esc_min_pulse=settings.ESC_MIN_PULSE,
            esc_max_pulse=settings.ESC_MAX_PULSE,
            servo_center=settings.SERVO_CENTER
        )
        
        # ESCアーミング
        print("\nESCアーミング中...")
        self.motor.drive(settings.SERVO_CENTER, 0.0)
        time.sleep(3)
        print("✓ アーミング完了")
        
        print("\n--- 初期化完了 ---")
        return True
    
    def _steering_to_servo(self, steering):
        """ステアリング値（-1.0〜1.0）をサーボ角度に変換"""
        if steering < 0:
            angle = settings.SERVO_CENTER + (steering * (settings.SERVO_CENTER - settings.SERVO_LEFT))
        else:
            angle = settings.SERVO_CENTER + (steering * (settings.SERVO_RIGHT - settings.SERVO_CENTER))
        
        return max(settings.SERVO_LEFT, min(settings.SERVO_RIGHT, angle))
    
    def run(self, duration=None):
        """自動運転を実行"""
        self.running = True
        start_time = time.time()
        loop_count = 0

        # ログ記録開始
        self.logger.start()

        print("\n" + "=" * 50)
        print("自動運転開始")
        print("終了するには Ctrl+C を押してください")
        print("=" * 50 + "\n")
        
        try:
            while self.running:
                loop_start = time.time()
                
                # 時間制限チェック
                if duration is not None:
                    elapsed = time.time() - start_time
                    if elapsed >= duration:
                        print(f"\n{duration}秒経過、終了します")
                        break
                
                # センサー読み取り (mm単位)
                distances = self.sensors.read()
                l2, l1, c, r1, r2 = distances
                
                # 緊急停止チェック
                if c >= settings.SENSOR_INVALID_VALUE or c < settings.EMERGENCY_STOP_DISTANCE:
                    if c < settings.EMERGENCY_STOP_DISTANCE:
                        print(f"⚠ 前方障害物検出 ({c}mm)、停止")
                    self.motor.stop(servo_center=settings.SERVO_CENTER)
                    time.sleep(0.1)
                    continue
                
                # 機械学習で予測 (mm単位で渡す)
                steering, class_name = self.predictor.predict(l2, l1, c, r1, r2)
                
                # ステアリングをサーボ角度に変換
                servo_angle = self._steering_to_servo(steering)
                
                # スロットル調整
                if c < settings.SLOW_DOWN_DISTANCE:
                    throttle = settings.THROTTLE_SLOW
                else:
                    throttle = self.base_throttle
                
                # モーター制御
                self.motor.drive(servo_angle, throttle)

                # データログ記録
                self.logger.log(servo_angle, throttle, distances, class_name)

                # デバッグ出力
                loop_count += 1
                if loop_count % settings.DEBUG_PRINT_INTERVAL == 0:
                    print(f"[{class_name:11}] "
                          f"L:{l2:4.0f} FL:{l1:4.0f} C:{c:4.0f} FR:{r1:4.0f} R:{r2:4.0f} | "
                          f"St:{servo_angle:5.1f}° Th:{throttle:+.2f}")
                
                # 制御周期
                elapsed_loop = time.time() - loop_start
                sleep_time = settings.CONTROL_INTERVAL - elapsed_loop
                if sleep_time > 0:
                    time.sleep(sleep_time)
        
        except KeyboardInterrupt:
            print("\n\n中断されました")
        
        finally:
            self.stop()
    
    def stop(self):
        """停止"""
        self.running = False
        self.logger.stop()
        if self.motor:
            self.motor.stop(servo_center=settings.SERVO_CENTER)
        print("停止しました")
    
    def cleanup(self):
        """クリーンアップ"""
        if self.motor:
            self.motor.cleanup()
        if self.sensors:
            self.sensors.cleanup()
        print("クリーンアップ完了")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='機械学習自動運転')
    parser.add_argument('--throttle', '-t', type=float, default=None,
                       help=f'スロットル値 (0.0-1.0、デフォルト: {settings.THROTTLE_NORMAL})')
    parser.add_argument('--duration', '-d', type=float, default=None,
                       help='実行時間（秒）')
    parser.add_argument('--no-log', action='store_true',
                       help='データログ記録を無効化')

    args = parser.parse_args()

    driver = MLDriver(throttle=args.throttle, enable_logging=not args.no_log)
    
    try:
        driver.initialize()
        
        input("\nEnterキーを押すと走行開始...")
        
        driver.run(duration=args.duration)
        
    except Exception as e:
        print(f"\nエラー: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.cleanup()


if __name__ == "__main__":
    main()