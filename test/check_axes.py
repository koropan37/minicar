#!/usr/bin/env python3
"""
コントローラーの全軸を確認するテストスクリプト
LTトリガーがどの軸に割り当てられているか確認するため
"""
import pygame
import time

pygame.init()
pygame.joystick.init()

joystick = pygame.joystick.Joystick(0)
joystick.init()

print(f"コントローラー: {joystick.get_name()}")
print(f"軸の数: {joystick.get_numaxes()}")
print(f"ボタンの数: {joystick.get_numbuttons()}")
print("\n全ての軸の値を表示します。LTを押して値が変化する軸を探してください。")
print("Ctrl+C で終了\n")

try:
    while True:
        pygame.event.pump()
        
        # 全軸の値を表示
        axes = []
        for i in range(joystick.get_numaxes()):
            axes.append(f"軸{i}:{joystick.get_axis(i):+.2f}")
        
        print(" | ".join(axes))
        time.sleep(0.2)

except KeyboardInterrupt:
    print("\n終了")
    joystick.quit()
    pygame.quit()
