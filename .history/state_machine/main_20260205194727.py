#!/usr/bin/env python3
"""
状態機械ベース走行 メインプログラム
左手法（左壁沿い）でコースを周回

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
from modules.state_controller import StateController, State

# ===========================================
# 周回設定（時間ベース）
# ===========================================
LAPS_TARGET = 3
ESTIMATED_LAP_SECONDS = 40.0  # 1周の目安時間（必要に応じて調整）
LAP_DETECTION_COOLDOWN = 6.0  # 周回検出の最短間隔（誤検出防止）


class MiniCarStateMachine:
    """状態機械ベース走行のメインクラス"""
    
    def __init__(self):
        print("=" * 50)
        print("状態機械ベース走行システム")
        print("左手法（左壁沿い）で周回")
        print("=" * 50)
        
        # I2Cバスを共有
        self.i2c = board.I2C()
        
        # 各モジュールの初期化
        self.sensor = SensorManager(self.i2c)
        self.motor = MotorController(self.i2c)
        self.controller = StateController()
        
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
        print(f"目標周回数: {LAPS_TARGET}周（停止はしません）")
        
        try:
            start_time = time.monotonic()
            next_lap_time = start_time + ESTIMATED_LAP_SECONDS
            last_lap_detect_time = start_time - LAP_DETECTION_COOLDOWN
            lap_count = 0
            lap_goal_announced = False

            while True:
                # 1. センサー読み取り
                sensor_data = self.sensor.read()
                
                # 2. 状態更新＆制御値計算
                steering, throttle = self.controller.update(sensor_data)
                
                # 3. モーター出力
                self.motor.drive(steering, throttle)
                
                # 4. デバッグ表示
                self.loop_count += 1
                if ENABLE_DEBUG_LOG and self.loop_count % DEBUG_PRINT_INTERVAL == 0:
                    print(self.controller.format_debug(sensor_data))

                # 4.5 周回判定（時間ベース + 安定走行状態）
                now = time.monotonic()
                if (
                    now >= next_lap_time
                    and (now - last_lap_detect_time) >= LAP_DETECTION_COOLDOWN
                    and self.controller.state == State.WALL_FOLLOW
                ):
                    lap_count += 1
                    last_lap_detect_time = now
                    next_lap_time = now + ESTIMATED_LAP_SECONDS
                    print(f"=== 周回完了: {lap_count}/{LAPS_TARGET} ===")

                    if lap_count >= LAPS_TARGET and not lap_goal_announced:
                        lap_goal_announced = True
                        print("=== 3周達成: 走行を継続します ===")
                
                # 5. 周期待ち
                time.sleep(CONTROL_INTERVAL)
                
        except KeyboardInterrupt:
            print("\n" + "-" * 50)
            print("停止信号を受信")
        
        finally:
            self.shutdown()
    
    def shutdown(self):
        """終了処理"""
        print("システム終了処理...")
        self.motor.cleanup()
        self.sensor.cleanup()
        print("正常に終了しました")


def main():
    """エントリーポイント"""
    car = MiniCarStateMachine()
    
    if not car.initialize():
        print("初期化に失敗しました。終了します。")
        sys.exit(1)
    
    print("\nEnterキーを押すと走行を開始します...")
    input()
    
    car.run()


if __name__ == "__main__":
    main()
