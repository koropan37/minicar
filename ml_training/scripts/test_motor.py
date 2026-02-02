#!/usr/bin/env python3
"""
モーター動作確認スクリプト
"""

import os
import sys
import time

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.append(project_root)

from modules import MLMotorController
from config import settings


def main():
    print("=" * 50)
    print("モーター動作テスト")
    print("=" * 50)
    
    motor = MLMotorController()
    motor.initialize(
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
    
    try:
        # 1. ステアリングテスト
        print("\n[1] ステアリングテスト")
        print("  中央 → 左 → 中央 → 右 → 中央")
        
        motor.drive(settings.SERVO_CENTER, 0.0)
        print(f"  中央 ({settings.SERVO_CENTER}°)")
        time.sleep(1)
        
        motor.drive(settings.SERVO_LEFT, 0.0)
        print(f"  左 ({settings.SERVO_LEFT}°)")
        time.sleep(1)
        
        motor.drive(settings.SERVO_CENTER, 0.0)
        print(f"  中央 ({settings.SERVO_CENTER}°)")
        time.sleep(1)
        
        motor.drive(settings.SERVO_RIGHT, 0.0)
        print(f"  右 ({settings.SERVO_RIGHT}°)")
        time.sleep(1)
        
        motor.drive(settings.SERVO_CENTER, 0.0)
        print(f"  中央 ({settings.SERVO_CENTER}°)")
        time.sleep(1)
        
        # 2. ESCアーミング
        print("\n[2] ESCアーミング（初期化）")
        print("  スロットル 0.0 を3秒間送信...")
        motor.drive(settings.SERVO_CENTER, 0.0)
        time.sleep(3)
        print("  ✓ アーミング完了（ピッと音がするはず）")
        
        # 3. スロットルテスト
        print("\n[3] スロットルテスト")
        print("  ⚠️ 車体を持ち上げてください！")
        input("  Enterキーを押すと前進テスト開始...")
        
        print("  スロットル 0.23（低速）で2秒間")
        motor.drive(settings.SERVO_CENTER, 0.23)
        time.sleep(2)
        
        print("  停止")
        motor.drive(settings.SERVO_CENTER, 0.0)
        time.sleep(1)
        
        print("  スロットル 0.28（通常）で2秒間")
        motor.drive(settings.SERVO_CENTER, 0.28)
        time.sleep(2)
        
        print("  停止")
        motor.drive(settings.SERVO_CENTER, 0.0)
        time.sleep(1)
        
        print("  スロットル 0.35（高速）で2秒間")
        motor.drive(settings.SERVO_CENTER, 0.35)
        time.sleep(2)
        
        print("  停止")
        motor.stop(servo_center=settings.SERVO_CENTER)
        
        print("\n✓ テスト完了")
    
    except KeyboardInterrupt:
        print("\n\n中断されました")
    
    finally:
        motor.cleanup()
        print("終了")


if __name__ == "__main__":
    main()