#!/usr/bin/env python3
"""
機械学習モデルを使った自動運転スクリプト
Raspberry Pi上で実行
"""

import os
import sys
import time
import argparse

# プロジェクトルートをパスに追加
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.append(project_root)

# 親ディレクトリ（minicar）もパスに追加
minicar_root = os.path.dirname(project_root)
sys.path.append(minicar_root)

from predict import MLPredictor

# state_machineのモジュールを流用
sys.path.append(os.path.join(minicar_root, 'state_machine'))
from modules.sensor import SensorManager
from modules.motor import MotorController

from config.settings import (
    THROTTLE_SLOW, THROTTLE_NORMAL, THROTTLE_STOP,
    SERVO_CENTER, SERVO_LEFT, SERVO_RIGHT,
    SENSOR_INVALID_VALUE
)


class MLDriver:
    """機械学習による自動運転クラス"""
    
    def __init__(self, throttle=0.28):
        """
        初期化
        
        Args:
            throttle: スロットル値（0.0〜1.0）
        """
        self.base_throttle = throttle
        self.running = False
        
        # 各モジュール
        self.predictor = None
        self.sensors = None
        self.motor = None
        
        print("=" * 50)
        print("機械学習自動運転システム")
        print("=" * 50)
        print(f"スロットル: {self.base_throttle}")
    
    def initialize(self):
        """初期化"""
        print("\n--- 初期化開始 ---")
        
        # 機械学習モデル
        print("\n[1/3] 機械学習モデル読み込み...")
        self.predictor = MLPredictor()
        
        # センサー
        print("\n[2/3] センサー初期化...")
        self.sensors = SensorManager()
        self.sensors.initialize()
        
        # モーター
        print("\n[3/3] モーター初期化...")
        self.motor = MotorController()
        self.motor.initialize()
        
        print("\n--- 初期化完了 ---")
        return True
    
    def _steering_to_servo(self, steering):
        """
        ステアリング値（-1.0〜1.0）をサーボ角度に変換
        
        Args:
            steering: -1.0（左）〜 0.0（直進）〜 1.0（右）
        
        Returns:
            サーボ角度（SERVO_LEFT〜SERVO_RIGHT）
        """
        # steering: -1.0 → SERVO_LEFT, 0.0 → SERVO_CENTER, 1.0 → SERVO_RIGHT
        if steering < 0:
            # 左方向
            angle = SERVO_CENTER + (steering * (SERVO_CENTER - SERVO_LEFT))
        else:
            # 右方向
            angle = SERVO_CENTER + (steering * (SERVO_RIGHT - SERVO_CENTER))
        
        return max(SERVO_LEFT, min(SERVO_RIGHT, angle))
    
    def run(self, duration=None):
        """
        自動運転を実行
        
        Args:
            duration: 実行時間（秒）。Noneの場合は無限ループ
        """
        self.running = True
        start_time = time.time()
        loop_count = 0
        
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
                
                # センサー読み取り
                sensor_data = self.sensors.read()
                l2 = sensor_data.left
                l1 = sensor_data.front_left
                c = sensor_data.center
                r1 = sensor_data.front_right
                r2 = sensor_data.right
                
                # 緊急停止チェック（前方センサー異常または非常に近い）
                if c >= SENSOR_INVALID_VALUE or c < 100:
                    if c < 100:
                        print(f"⚠ 前方障害物検出 ({c}mm)、停止")
                    self.motor.stop()
                    time.sleep(0.1)
                    continue
                
                # 機械学習で予測
                steering, class_name = self.predictor.predict(l2, l1, c, r1, r2)
                
                # ステアリングをサーボ角度に変換
                servo_angle = self._steering_to_servo(steering)
                
                # スロットル調整（前方が近いときは減速）
                if c < 300:
                    throttle = THROTTLE_SLOW
                else:
                    throttle = self.base_throttle
                
                # モーター制御
                self.motor.drive(servo_angle, throttle)
                
                # デバッグ出力（5回に1回）
                loop_count += 1
                if loop_count % 5 == 0:
                    print(f"[{class_name:11}] "
                          f"L:{l2:4.0f} FL:{l1:4.0f} C:{c:4.0f} FR:{r1:4.0f} R:{r2:4.0f} | "
                          f"St:{servo_angle:5.1f} Th:{throttle:+.2f}")
                
                # 制御周期（約25Hz）
                elapsed_loop = time.time() - loop_start
                sleep_time = 0.04 - elapsed_loop
                if sleep_time > 0:
                    time.sleep(sleep_time)
        
        except KeyboardInterrupt:
            print("\n\n中断されました")
        
        finally:
            self.stop()
    
    def stop(self):
        """停止"""
        self.running = False
        if self.motor:
            self.motor.stop()
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
    parser.add_argument('--throttle', '-t', type=float, default=0.28,
                       help='スロットル値 (0.0-1.0、デフォルト: 0.28)')
    parser.add_argument('--duration', '-d', type=float, default=None,
                       help='実行時間（秒）。省略すると無限ループ')
    
    args = parser.parse_args()
    
    driver = MLDriver(throttle=args.throttle)
    
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