#!/usr/bin/env python3
"""
ジョイスティック操作 + センサー連携 + 録画機能
メインプログラム

使い方:
    python main.py

操作方法:
    - 左スティック X軸: ステアリング（左右）
    - 左スティック Y軸: スロットル（前進/後退）
    - Aボタン: 録画開始
    - Bボタン: 録画停止・保存
    - Xボタン: 緊急停止
    - Ctrl+C: プログラム終了
"""

import sys
import os
import time
import board

# パスを追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import RECORD_INTERVAL
from modules.sensor import SensorManager
from modules.motor import MotorController
from modules.joystick import JoystickController
from modules.recorder import DataRecorder


def main():
    """メイン関数"""
    print("=" * 50)
    print("ミニカー ジョイスティック制御システム")
    print("=" * 50)
    print()
    print("操作方法:")
    print("  左スティック X軸: ステアリング（左右）")
    print("  左スティック Y軸: スロットル（前進/後退）")
    print("  Aボタン: 録画開始")
    print("  Bボタン: 録画停止・保存")
    print("  Xボタン: 緊急停止")
    print("  Ctrl+C: プログラム終了")
    print("=" * 50)
    print()
    
    # I2Cバスを共有
    i2c = board.I2C()
    
    # 各モジュールの初期化
    sensor_manager = SensorManager(i2c)
    motor_controller = MotorController(i2c)
    joystick_controller = JoystickController()
    data_recorder = DataRecorder()
    
    try:
        # センサー初期化
        print("[1/3] センサーを初期化中...")
        sensor_manager.initialize()
        
        # モーター初期化
        print("[2/3] モーターを初期化中...")
        motor_controller.initialize()
        
        # ジョイスティック初期化
        print("[3/3] ジョイスティックを初期化中...")
        if not joystick_controller.initialize():
            print("警告: ジョイスティックなしで続行します（センサーテストモード）")
        
        print()
        print("初期化完了！制御を開始します...")
        print("-" * 50)
        
        # 前回のボタン状態（エッジ検出用）
        prev_record_start = False
        prev_record_stop = False
        prev_emergency = False
        
        # メインループ
        while True:
            loop_start = time.time()
            
            # ジョイスティック入力を取得
            inputs = joystick_controller.get_all_inputs()
            steering = inputs['steering']
            throttle = inputs['throttle']
            
            # センサーデータを取得
            distances = sensor_manager.read_distances()
            L2, L1, C, R1, R2 = distances
            
            # ボタン処理（立ち上がりエッジで検出）
            # 録画開始ボタン
            if inputs['record_start'] and not prev_record_start:
                data_recorder.start_recording()
            prev_record_start = inputs['record_start']
            
            # 録画停止ボタン
            if inputs['record_stop'] and not prev_record_stop:
                data_recorder.stop_recording()
            prev_record_stop = inputs['record_stop']
            
            # 緊急停止ボタン
            if inputs['emergency_stop'] and not prev_emergency:
                motor_controller.stop()
                print("緊急停止！")
                steering = 0
                throttle = 0
            prev_emergency = inputs['emergency_stop']
            
            # モーター制御
            if not inputs['emergency_stop']:
                actual_angle = motor_controller.set_steering(steering)
                actual_throttle = motor_controller.set_throttle(throttle)
            else:
                actual_angle = motor_controller.steering_servo.angle
                actual_throttle = 0
            
            # 録画中ならデータを記録
            if data_recorder.is_recording():
                data_recorder.record(steering, throttle, distances)
            
            # ステータス表示
            rec_status = "●REC" if data_recorder.is_recording() else "    "
            rec_count = data_recorder.get_record_count()
            print(f"{rec_status} | Steer:{steering:+.2f} Throttle:{throttle:+.2f} | "
                  f"Dist[L2={L2:3.0f} L1={L1:3.0f} C={C:3.0f} R1={R1:3.0f} R2={R2:3.0f}] | "
                  f"Count:{rec_count}")
            
            # ループ間隔を調整
            elapsed = time.time() - loop_start
            sleep_time = RECORD_INTERVAL - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    except KeyboardInterrupt:
        print("\n\nCtrl+C が押されました。終了します...")
    
    finally:
        # 録画中なら保存
        if data_recorder.is_recording():
            print("録画データを保存中...")
            data_recorder.stop_recording()
        
        # クリーンアップ
        print("クリーンアップ中...")
        motor_controller.cleanup()
        sensor_manager.cleanup()
        joystick_controller.cleanup()
        print("終了しました")


if __name__ == "__main__":
    main()
