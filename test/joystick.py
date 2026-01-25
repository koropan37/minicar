import pygame
import time

# 初期化
pygame.init()
pygame.joystick.init()

try:
    # ジョイスティックの取得（0番目のデバイス）
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"Controller Name: {joystick.get_name()}")
except pygame.error:
    print("コントローラーが見つかりません。")
    exit()

try:
    while True:
        # イベントを取得（これを呼ばないと値が更新されません）
        pygame.event.pump()

        # 左スティックの値を取得 (-1.0 ～ 1.0)
        # axis 0: 左右 (左が-1, 右が1)
        # axis 1: 上下 (上が-1, 下が1) ※環境により逆の場合あり
        left_x = joystick.get_axis(0)
        left_y = joystick.get_axis(1)

        # ボタンの取得 (0 または 1)
        # button 0: Aボタン (XInputモード時)
        button_a = joystick.get_button(0)

        # 動作確認用の表示
        print(f"Stick X: {left_x:.2f} | Stick Y: {left_y:.2f} | Button A: {button_a}")

        time.sleep(0.1)

except KeyboardInterrupt:
    print("終了します")
    joystick.quit()
    pygame.quit()