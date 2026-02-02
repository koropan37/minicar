"""
センサー管理モジュール（VL53L4CD × 5）
"""

import time
import board
import busio
import digitalio
import adafruit_vl53l4cd


class MLSensorManager:
    """センサー管理（VL53L4CD × 5）"""
    
    def __init__(self):
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.sensors = []
    
    def initialize(self, xshut_pins, base_address=0x30, 
                   timing_budget=20, inter_measurement=0,
                   invalid_value=9999):
        """
        センサー初期化
        
        Args:
            xshut_pins: XSHUTピンのリスト（GPIO番号）
            base_address: ベースI2Cアドレス
            timing_budget: タイミングバジェット (ms)
            inter_measurement: 測定間隔 (ms)
            invalid_value: 無効値
        """
        print("センサー初期化中...")
        
        self.invalid_value = invalid_value
        
        # アドレスリスト生成
        addresses = [base_address + i for i in range(len(xshut_pins))]
        
        # 全センサーをシャットダウン
        xshut_controls = []
        for pin in xshut_pins:
            xshut = digitalio.DigitalInOut(getattr(board, f'D{pin}'))
            xshut.direction = digitalio.Direction.OUTPUT
            xshut.value = False
            xshut_controls.append(xshut)
        
        time.sleep(0.1)
        
        # 1つずつ起動してアドレス変更
        for i, (xshut, addr) in enumerate(zip(xshut_controls, addresses)):
            xshut.value = True
            time.sleep(0.1)
            
            sensor = adafruit_vl53l4cd.VL53L4CD(self.i2c)
            sensor.set_address(addr)
            sensor.inter_measurement = inter_measurement
            sensor.timing_budget = timing_budget
            sensor.start_ranging()
            
            self.sensors.append(sensor)
            print(f"  センサー {i+1}/{len(xshut_pins)} 初期化完了 (0x{addr:02X})")
        
        print("✓ 全センサー初期化完了")
    
    def read(self):
        """全センサー読み取り (mm単位)"""
        distances = []
        for sensor in self.sensors:
            while not sensor.data_ready:
                pass
            sensor.clear_interrupt()
            distance = sensor.distance if sensor.distance is not None else self.invalid_value
            distances.append(distance)
        
        return distances  # [L2, L1, C, R1, R2]
    
    def cleanup(self):
        """クリーンアップ"""
        for sensor in self.sensors:
            sensor.stop_ranging()