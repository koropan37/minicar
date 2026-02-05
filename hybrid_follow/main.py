#!/usr/bin/env python3
"""
ハイブリッド走行 メインプログラム
状況に応じて左壁、右壁、中央維持を切り替えて走行

使用方法:
    python main.py
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
from modules.hybrid_controller import HybridController


class MiniCarHybrid:
    """ハイブリッド走行のメインクラス"""
    
    def __init__(self):
        print("=" * 50)
        print("ハイブリッド（適応型）走行システム")
        print("左壁・右壁・中央維持を自動切替")
        print("=" * 50)
        
        self.i2c = board.I2C()
        self.sensor = SensorManager(self.i2c)
        self.motor = MotorController(self.i2c)
        self.controller = HybridController()
        
        self.loop_count = 0
    
    def initialize(self):
        try:
            self.sensor.initialize()
            self.motor.initialize()
            print("初期化完了！")
            return True
        except Exception as e:
            print(f"初期化エラー: {e}")
            return False
    
    def run(self):
        print("\n走行開始！ (Ctrl+C で停止)")
        try:
            while True:
                sensor_data = self.sensor.read()
                steering, throttle = self.controller.update(sensor_data)
                self.motor.drive(steering, throttle)
                
                self.loop_count += 1
                if ENABLE_DEBUG_LOG and self.loop_count % DEBUG_PRINT_INTERVAL == 0:
                    print(self.controller.format_debug(sensor_data))
                
                time.sleep(CONTROL_INTERVAL)
                
        except KeyboardInterrupt:
            print("\n停止信号を受信")
        finally:
            self.shutdown()
    
    def shutdown(self):
        self.motor.cleanup()
        self.sensor.cleanup()
        print("終了しました")


def main():
    car = MiniCarHybrid()
    if not car.initialize():
        sys.exit(1)
    
    print("\nEnterキーを押すと走行を開始します...")
    input()
    car.run()


if __name__ == "__main__":
    main()
