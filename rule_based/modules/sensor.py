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
        """
        センサーの初期化処理
        
        Returns:
            bool: 初期化成功時True
        """
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
                
                labels = ["左外", "左内", "正面", "右内", "右外"]
                print(f"  センサー{i} ({labels[i]}): 0x{new_address:02X} で初期化完了")
                
            except Exception as e:
                print(f"  センサー{i} 初期化エラー: {e}")
                self.sensors.append(None)
        
        active_count = sum(1 for s in self.sensors if s is not None)
        if active_count == 0:
            raise RuntimeError("エラー: センサーが1つも初期化できませんでした")
        
        print(f"センサー初期化完了: {active_count}/5 個が有効")
        return True
    
    def read_distances(self):
        """
        全センサーから距離を読み取る
        
        Returns:
            list: [L_out, L_in, Center, R_in, R_out] の距離リスト (mm)
        """
        distances = []
        
        for idx, sensor in enumerate(self.sensors):
            if sensor is None:
                distances.append(SENSOR_INVALID_VALUE)
                continue
                
            try:
                # タイムアウト付きでデータ待ち
                timeout = 0
                while not sensor.data_ready:
                    time.sleep(0.001)
                    timeout += 1
                    if timeout > 50:  # 50ms タイムアウト
                        distances.append(SENSOR_INVALID_VALUE)
                        break
                else:
                    sensor.clear_interrupt()
                    # VL53L4CDライブラリはcmで返すのでmmに変換
                    dist_mm = sensor.distance * 10
                    
                    # 無効な値のチェック
                    if dist_mm <= 0 or dist_mm > 3000:
                        dist_mm = SENSOR_INVALID_VALUE
                    distances.append(dist_mm)
                    
            except Exception as e:
                distances.append(SENSOR_INVALID_VALUE)
        
        # センサー数が足りない場合は無効値で埋める
        while len(distances) < 5:
            distances.append(SENSOR_INVALID_VALUE)
        
        return distances[:5]
    
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
