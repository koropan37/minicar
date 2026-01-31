"""
ジョイスティック制御モジュール
"""

import pygame
import time

import sys
sys.path.append('..')
from config.settings import (
    JOYSTICK_DEADZONE,
    AXIS_STEERING, AXIS_THROTTLE,
    BUTTON_RECORD_START, BUTTON_RECORD_STOP, BUTTON_EMERGENCY_STOP
)


class JoystickController:
    """ジョイスティック制御クラス"""
    
    def __init__(self):
        """ジョイスティックコントローラーの初期化"""
        self.joystick = None
        self.connected = False
        
    def initialize(self):
        """ジョイスティックの初期化処理"""
        pygame.init()
        pygame.joystick.init()
        
        try:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            self.connected = True
            print(f"ジョイスティック接続: {self.joystick.get_name()}")
            print(f"ボタン数: {self.joystick.get_numbuttons()}")
            print(f"軸数: {self.joystick.get_numaxes()}")
            return True
        except pygame.error:
            print("コントローラーが見つかりません")
            self.connected = False
            return False
    
    def _apply_deadzone(self, value):
        """デッドゾーンを適用"""
        if abs(value) < JOYSTICK_DEADZONE:
            return 0.0
        return value
    
    def get_steering(self):
        """
        ステアリング値を取得
        
        Returns:
            float: -1.0（左）〜 1.0（右）
        """
        if not self.connected:
            return 0.0
        pygame.event.pump()
        value = self.joystick.get_axis(AXIS_STEERING)
        return self._apply_deadzone(value)
    
    def get_throttle(self):
        """
        スロットル値を取得（Y軸は反転: 上が-1なので反転）
        
        Returns:
            float: -1.0（後退）〜 1.0（前進）
        """
        if not self.connected:
            return 0.0
        pygame.event.pump()
        value = -self.joystick.get_axis(AXIS_THROTTLE)  # Y軸反転
        return self._apply_deadzone(value)
    
    def get_button(self, button_id):
        """
        ボタンの状態を取得
        
        Args:
            button_id: ボタン番号
            
        Returns:
            bool: 押されている場合True
        """
        if not self.connected:
            return False
        pygame.event.pump()
        return self.joystick.get_button(button_id) == 1
    
    def is_record_start_pressed(self):
        """録画開始ボタンが押されているか"""
        return self.get_button(BUTTON_RECORD_START)
    
    def is_record_stop_pressed(self):
        """録画停止ボタンが押されているか"""
        return self.get_button(BUTTON_RECORD_STOP)
    
    def is_emergency_stop_pressed(self):
        """緊急停止ボタンが押されているか"""
        return self.get_button(BUTTON_EMERGENCY_STOP)
    
    def get_all_inputs(self):
        """
        全ての入力を一度に取得
        
        Returns:
            dict: ステアリング、スロットル、ボタン状態
        """
        pygame.event.pump()
        return {
            'steering': self._apply_deadzone(self.joystick.get_axis(AXIS_STEERING)),
            'throttle': self._apply_deadzone(-self.joystick.get_axis(AXIS_THROTTLE)),
            'record_start': self.joystick.get_button(BUTTON_RECORD_START) == 1,
            'record_stop': self.joystick.get_button(BUTTON_RECORD_STOP) == 1,
            'emergency_stop': self.joystick.get_button(BUTTON_EMERGENCY_STOP) == 1
        }
    
    def cleanup(self):
        """ジョイスティックのクリーンアップ"""
        if self.joystick:
            self.joystick.quit()
        pygame.quit()
        print("ジョイスティックをクリーンアップしました")
