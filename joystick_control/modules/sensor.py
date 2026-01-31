"""
センサーモジュール (VL53L4CD)
test_sensor.py の設定を参考に作成
"""

import board
import time
from digitalio import DigitalInOut, Direction
import adafruit_vl53l4cd

import sys
sys.path.append('..')
from config.settings import (
    XSHUT_PINS, SENSOR_BASE_ADDRESS, 
    SENSOR_TIMING_BUDGET, SENSOR_INTER_MEASUREMENT,
    SENSOR_INVALID_VALUE
)


class SensorManager:
    """VL53L4CDセンサーを管理するクラス"""
    
    def __init__(self, i2c=None):
        """
        センサーマネージャーの初期化
        
        Args:
            i2c: I2Cバスインスタンス（Noneの場合は自動作成）
        """
        self.i2c = i2c if i2c else board.I2C()
        self.sensors = []
        self.xshuts = []
        
    def initialize(self):
        """センサーの初期化処理"""
        # XSHUTピンの設定
        for pin in XSHUT_PINS:
            gpio = DigitalInOut(getattr(board, f"D{pin}"))
            gpio.direction = Direction.OUTPUT
            gpio.value = False  # 一旦すべてOFFにする
            self.xshuts.append(gpio)
        
        time.sleep(0.1)  # すべてOFFになるのを待つ
        
        # 1つずつ起こしてアドレスを変更
        for i, xshut in enumerate(self.xshuts):
            xshut.value = True  # センサをON
            time.sleep(0.05)    # 起動を確実に待つ
            
            try:
                # 新しいセンサインスタンスを作成
                sensor = adafruit_vl53l4cd.VL53L4CD(self.i2c)
                
                # アドレスを変更
                new_address = SENSOR_BASE_ADDRESS + i
                sensor.set_address(new_address)
                time.sleep(0.01)
                
                # センサーの設定
                sensor.timing_budget = SENSOR_TIMING_BUDGET
                sensor.inter_measurement = SENSOR_INTER_MEASUREMENT
                
                # 距離測定を開始
                sensor.start_ranging()
                self.sensors.append(sensor)
                print(f"Sensor {i} initialized at address {hex(new_address)}")
            except Exception as e:
                print(f"Error initializing sensor {i}: {e}")
                continue
        
        if len(self.sensors) == 0:
            raise RuntimeError("エラー: センサーが1つも初期化できませんでした")
        
        print(f"{len(self.sensors)}個のセンサーが初期化されました")
        return True
    
    def read_distances(self):
        """
        全センサーから距離を読み取る
        
        Returns:
            list: [L2, L1, C, R1, R2] の距離リスト (cm)
        """
        distances = []
        
        for idx, sensor in enumerate(self.sensors):
            try:
                # タイムアウト付きでデータ待ち
                timeout = 0
                while not sensor.data_ready:
                    time.sleep(0.001)
                    timeout += 1
                    if timeout > 100:  # 100ms タイムアウト
                        print(f"Sensor {idx} timeout")
                        distances.append(SENSOR_INVALID_VALUE)
                        break
                else:
                    sensor.clear_interrupt()
                    dist = sensor.distance
                    # 無効な値は大きな値に置き換え
                    if dist == 0 or dist is None:
                        dist = SENSOR_INVALID_VALUE
                    distances.append(dist)
            except Exception as e:
                print(f"Error reading sensor {idx}: {e}")
                distances.append(SENSOR_INVALID_VALUE)
        
        # センサー数が足りない場合は無効値で埋める
        while len(distances) < 5:
            distances.append(SENSOR_INVALID_VALUE)
        
        return distances[:5]  # [L2, L1, C, R1, R2]
    
    def cleanup(self):
        """センサーのクリーンアップ"""
        for xshut in self.xshuts:
            xshut.value = False
        print("センサーをクリーンアップしました")
