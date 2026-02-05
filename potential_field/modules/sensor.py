"""
センサーモジュール (VL53L4CD)
5つの距離センサーを管理
"""

import board
import time
from digitalio import DigitalInOut, Direction
import adafruit_vl53l4cd

from config.settings import (
    XSHUT_PINS, SENSOR_BASE_ADDRESS,
    SENSOR_TIMING_BUDGET, SENSOR_INTER_MEASUREMENT,
    SENSOR_INVALID_VALUE, SENSOR_MAX_RANGE
)


class SensorData:
    """センサーデータを格納する構造体"""
    __slots__ = ['left', 'front_left', 'center', 'front_right', 'right', 'timestamp']
    
    def __init__(self, distances=None):
        if distances and len(distances) >= 5:
            self.left = distances[0]
            self.front_left = distances[1]
            self.center = distances[2]
            self.front_right = distances[3]
            self.right = distances[4]
        else:
            self.left = SENSOR_INVALID_VALUE
            self.front_left = SENSOR_INVALID_VALUE
            self.center = SENSOR_INVALID_VALUE
            self.front_right = SENSOR_INVALID_VALUE
            self.right = SENSOR_INVALID_VALUE
        self.timestamp = time.monotonic()
    
    def as_list(self):
        return [self.left, self.front_left, self.center, self.front_right, self.right]
    
    def __repr__(self):
        return f"L:{self.left:4.0f} FL:{self.front_left:4.0f} C:{self.center:4.0f} FR:{self.front_right:4.0f} R:{self.right:4.0f}"


class SensorManager:
    """VL53L4CDセンサーを管理するクラス"""
    
    LABELS = ["真左", "斜め左前", "正面", "斜め右前", "真右"]
    
    def __init__(self, i2c=None):
        self.i2c = i2c if i2c else board.I2C()
        self.sensors = []
        self.xshuts = []
        self._last_data = SensorData()
        
    def initialize(self):
        """センサーの初期化処理"""
        print("センサー初期化開始...")
        
        # XSHUTピンの設定（全センサーをOFFにする）
        for pin in XSHUT_PINS:
            gpio = DigitalInOut(getattr(board, f"D{pin}"))
            gpio.direction = Direction.OUTPUT
            gpio.value = False
            self.xshuts.append(gpio)
        
        time.sleep(0.1)
        
        # 1つずつONにしてアドレスを変更
        for i, xshut in enumerate(self.xshuts):
            xshut.value = True
            time.sleep(0.05)
            
            try:
                sensor = adafruit_vl53l4cd.VL53L4CD(self.i2c)
                new_address = SENSOR_BASE_ADDRESS + i
                sensor.set_address(new_address)
                time.sleep(0.01)
                
                sensor.timing_budget = SENSOR_TIMING_BUDGET
                sensor.inter_measurement = SENSOR_INTER_MEASUREMENT
                sensor.start_ranging()
                self.sensors.append(sensor)
                
                print(f"  センサー{i} ({self.LABELS[i]}): 0x{new_address:02X} OK")
                
            except Exception as e:
                print(f"  センサー{i} ({self.LABELS[i]}): エラー - {e}")
                self.sensors.append(None)
        
        active_count = sum(1 for s in self.sensors if s is not None)
        if active_count == 0:
            raise RuntimeError("センサーが1つも初期化できませんでした")
        
        print(f"センサー初期化完了: {active_count}/5 個が有効")
        return True
    
    def read(self):
        """
        全センサーから距離を読み取る
        
        Returns:
            SensorData: センサーデータオブジェクト
        """
        distances = []
        
        for idx, sensor in enumerate(self.sensors):
            if sensor is None:
                distances.append(SENSOR_INVALID_VALUE)
                continue
                
            try:
                timeout = 0
                while not sensor.data_ready:
                    time.sleep(0.001)
                    timeout += 1
                    if timeout > 50:
                        distances.append(SENSOR_INVALID_VALUE)
                        break
                else:
                    sensor.clear_interrupt()
                    # VL53L4CDはcmで返すのでmmに変換
                    dist_mm = sensor.distance * 10
                    
                    # 範囲外チェック
                    if dist_mm <= 0 or dist_mm > SENSOR_MAX_RANGE:
                        dist_mm = SENSOR_INVALID_VALUE
                    distances.append(dist_mm)
                    
            except Exception:
                distances.append(SENSOR_INVALID_VALUE)
        
        # 足りない場合は無効値で埋める
        while len(distances) < 5:
            distances.append(SENSOR_INVALID_VALUE)
        
        self._last_data = SensorData(distances[:5])
        return self._last_data
    
    @property
    def last_data(self):
        """最後に読み取ったデータを返す"""
        return self._last_data
    
    def cleanup(self):
        """センサーのクリーンアップ"""
        for sensor in self.sensors:
            if sensor is not None:
                try:
                    sensor.stop_ranging()
                except:
                    pass
        
        for xshut in self.xshuts:
            xshut.value = False
            
        print("センサーをクリーンアップしました")
