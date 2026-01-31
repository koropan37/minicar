"""
ジョイスティック制御モジュール
"""

import pygame
import time

import sys
sys.path.append('..')
from config.settings import (
    JOYSTICK_DEADZONE,
    AXIS_STEERING, AXIS_TRIGGER_RIGHT, AXIS_TRIGGER_LEFT,
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
        
        # トリガーの値を取得
        # 離している: -1.0、全押し: 1.0
        rt_raw = self.joystick.get_axis(AXIS_TRIGGER_RIGHT)
        lt_raw = self.joystick.get_axis(AXIS_TRIGGER_LEFT)
        
        # -1.0〜1.0 を 0.0〜1.0 に正規化
        rt = (rt_raw + 1.0) / 2.0
        lt = (lt_raw + 1.0) / 2.0
        
        # スロットル計算: 
        # - 何も押してない → 0（停止）
        # - 右トリガー押し → 前進（0.0〜1.0）
        # - 左トリガー押し → 後退（-1.0〜0.0）
        # - 両方押し → 前進優先
        if rt > JOYSTICK_DEADZONE:
            throttle = rt
        elif lt > JOYSTICK_DEADZONE:
            throttle = -lt
        else:
            throttle = 0.0  # 自動停止
        
        return {
            'steering': self._apply_deadzone(self.joystick.get_axis(AXIS_STEERING)),
            'throttle': throttle,
            'forward_trigger': rt,   # 前進トリガー（RT）0.0〜1.0
            'reverse_trigger': lt,   # 後退トリガー（LT）0.0〜1.0
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
