#!/usr/bin/env python3
"""
ルールベース走行 メインプログラム
左壁沿いに走行するミニカー制御

使用方法:
    python main.py
    
停止方法:
    Ctrl+C
"""

import time
import board
import sys

from config.settings import (
    CONTROL_INTERVAL,
    DEBUG_PRINT_INTERVAL,
    ENABLE_DEBUG_LOG
)
from modules.sensor import SensorManager
from modules.motor import MotorController
from modules.controller import DrivingController
from modules.data_logger import DataLogger


class MiniCarRuleBased:
    """ルールベース走行のメインクラス"""

    def __init__(self, enable_logging=True):
        """初期化"""
        print("=" * 50)
        print("ルールベース走行システム 初期化")
        print("=" * 50)

        # I2Cバスを共有
        self.i2c = board.I2C()

        # 各モジュールの初期化
        self.sensor = SensorManager(self.i2c)
        self.motor = MotorController(self.i2c)
        self.controller = DrivingController()

        # データロガー
        self.logger = DataLogger(enabled=enable_logging)

        # ループカウンター
        self.loop_count = 0
    
    def initialize(self):
        """システムの初期化"""
        try:
            self.sensor.initialize()
            self.motor.initialize()
            print("=" * 50)
            print("初期化完了！")
            print("=" * 50)
            return True
        except Exception as e:
            print(f"初期化エラー: {e}")
            return False
    
    def run(self):
        """メインループ"""
        print("\n走行開始！ (Ctrl+C で停止)")
        print("-" * 50)

        # ログ記録開始
        self.logger.start()

        try:
            while True:
                # 1. センサー読み取り
                distances = self.sensor.read_distances()

                # 2. 制御値の計算
                steering, throttle, state = self.controller.compute_control(distances)

                # 3. モーター出力
                self.motor.set_steering_angle(steering)
                self.motor.set_throttle(throttle)

                # 4. データログ記録
                self.logger.log(steering, throttle, distances, state)

                # 5. デバッグ表示
                self.loop_count += 1
                if ENABLE_DEBUG_LOG and self.loop_count % DEBUG_PRINT_INTERVAL == 0:
                    debug_msg = self.controller.format_debug_info(distances, steering, throttle)
                    print(debug_msg)

                # 6. 周期待ち
                time.sleep(CONTROL_INTERVAL)

        except KeyboardInterrupt:
            print("\n" + "-" * 50)
            print("停止信号を受信しました")

        finally:
            self.shutdown()
    
    def shutdown(self):
        """終了処理"""
        print("システム終了処理...")
        self.logger.stop()
        self.motor.cleanup()
        self.sensor.cleanup()
        print("正常に終了しました")


def main():
    """エントリーポイント"""
    import argparse

    parser = argparse.ArgumentParser(description='ルールベース走行システム')
    parser.add_argument('--no-log', action='store_true',
                       help='データログ記録を無効化')
    args = parser.parse_args()

    car = MiniCarRuleBased(enable_logging=not args.no_log)

    if not car.initialize():
        print("初期化に失敗しました。終了します。")
        sys.exit(1)

    # 開始前の確認
    print("\nEnterキーを押すと走行を開始します...")
    input()

    car.run()


if __name__ == "__main__":
    main()
